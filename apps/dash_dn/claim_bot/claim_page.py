from __future__ import annotations

import re
import time
from dataclasses import dataclass

from playwright.sync_api import Page, expect


@dataclass
class UiServiceRow:
    index: int
    code: str
    begin_date: str
    end_date: str
    qty: str
    doctor: str = ""


def _norm(s: str) -> str:
    return str(s or "").strip()


def _to_ui_date(raw: str) -> str:
    """UI ожидает короткий формат dd-mm-yy (как на форме)."""
    s = _norm(raw)
    if not s:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        yy = m.group(1)[-2:]
        return f"{m.group(3)}-{m.group(2)}-{yy}"
    m = re.match(r"^(\d{2})[-.](\d{2})[-.](\d{4})$", s)
    if m:
        yy = m.group(3)[-2:]
        return f"{m.group(1)}-{m.group(2)}-{yy}"
    m = re.match(r"^(\d{2})-(\d{2})-(\d{2})$", s)
    if m:
        return s
    return s


_SVC_BASE_RE = re.compile(r"^([AB]\d{2}\.\d{2,3}\.\d{3})(?:\.\d{3})?$", re.IGNORECASE)
_SVC_ANY_RE = re.compile(r"\b([AB]\d{2}\.\d{2,3}\.\d{3}(?:\.\d{3})?)\b", re.IGNORECASE)


def _svc_base(code: str) -> str:
    c = _norm(code).upper()
    m = _SVC_BASE_RE.match(c)
    return m.group(1) if m else c

class ClaimPage:
    def extract_visible_service_codes(self) -> set[str]:
        """Извлекает коды услуг из видимых текстов (fallback для режима просмотра)."""
        codes: set[str] = set()
        # 1) По тексту (не всегда доступен)
        for el in self.page.locator(".Selected-item").all():
            try:
                txt = _norm(el.inner_text(timeout=500))
            except Exception:
                txt = ""
            for m in _SVC_ANY_RE.finditer(txt):
                codes.add(m.group(1).upper())
        # 2) По title у Select-value (обычно содержит "CODE Описание")
        for el in self.page.locator("div.Select-value[title]").all():
            title = _norm(el.get_attribute("title") or "")
            for m in _SVC_ANY_RE.finditer(title):
                codes.add(m.group(1).upper())
        return codes

    def __init__(self, page: Page, *, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/") + "/"

    def open_talon(self, talon_id: str) -> None:
        url = self.base_url + str(talon_id).strip()
        self.page.goto(url, wait_until="domcontentloaded")

    def wait_ready(self, timeout_ms: int = 60_000) -> None:
        # Минимальный сигнал готовности: появилась кнопка добавления услуги
        add_btn = self.page.locator("#add-service").first
        expect(add_btn).to_be_visible(timeout=timeout_ms)
        # Часто сверху висит модалка "Пожалуйста, подождите..." и кнопки disabled.
        for sel in [
            "text=Пожалуйста, подождите",
            "text=Подождите",
            "[role='dialog']",
        ]:
            try:
                self.page.locator(sel).first.wait_for(state="hidden", timeout=timeout_ms)
            except Exception:
                pass
        # Дожидаемся, что можно добавлять услуги
        try:
            expect(add_btn).to_be_enabled(timeout=timeout_ms)
        except Exception:
            pass
        self._ensure_editable(timeout_ms=timeout_ms)

    def _ensure_editable(self, timeout_ms: int = 30_000) -> None:
        """Некоторые талоны открываются в режиме просмотра; включаем редактирование best-effort."""
        add_btn = self.page.locator("#add-service").first
        try:
            if add_btn.is_enabled():
                return
        except Exception:
            pass

        # Пытаемся нажать "Редактировать/Изменить" если есть
        candidates = [
            "button:has-text('Редактировать')",
            "button:has-text('Изменить')",
            "button:has-text('Открыть на редактирование')",
            "button[aria-label='edit']",
            "button[title*='Редакт']",
        ]
        for sel in candidates:
            loc = self.page.locator(sel).first
            if loc.count():
                try:
                    loc.click(timeout=3_000)
                except Exception:
                    try:
                        loc.click(force=True)
                    except Exception:
                        pass
                break

        # ждём, что add-service станет активной
        try:
            expect(add_btn).to_be_enabled(timeout=timeout_ms)
        except Exception:
            # оставим как есть — дальше упадём с понятной ошибкой в add_empty_row
            return

    def save(self, timeout_ms: int = 30_000) -> None:
        """Сохраняет талон и проверяет toast-ошибки валидации."""
        # 1) Кнопка "СОХРАНИТЬ (F2)" / "Сохранить"
        btn = None
        try:
            btn = self.page.get_by_role("button", name=re.compile("сохран", re.I)).first
        except Exception:
            btn = None
        if btn is None or btn.count() == 0:
            btn = self.page.locator("button:has-text('Сохран')").first
        if btn.count():
            try:
                btn.click(timeout=5_000)
            except Exception:
                btn.click(force=True)
        else:
            # 2) F2 как fallback
            self.page.keyboard.press("F2")

        # ждём завершения запроса
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            pass

        # Проверяем красный toast (на скрине: "Заполните обязательные поля")
        err_toast = self.page.locator("text=Заполните обязательные поля").first
        if err_toast.count():
            raise RuntimeError("Сохранение отклонено: заполните обязательные поля (toast).")

    def verify_expected_present(self, expected: list[dict]) -> dict:
        """Проверка: все ожидаемые коды присутствуют."""
        current = self.read_services()
        have_full = {r.code for r in current if r.code}
        have_base = {_svc_base(r.code) for r in current if r.code}
        if not have_full:
            codes = self.extract_visible_service_codes()
            have_full = codes
            have_base = {_svc_base(c) for c in codes}
        need_full = {_norm(x.get("code")).upper() for x in expected if _norm(x.get("code"))}
        need_base = {_svc_base(x) for x in need_full}
        missing = sorted([c for c in need_base if c not in have_base])
        return {
            "need": len(need_base),
            "have": len(have_base),
            "missing": missing,
            "have_full_n": len(have_full),
        }

    def verify_exact_set_edit(self, expected: list[dict]) -> dict:
        """Строгая проверка в edit-режиме по combobox-service-*."""
        rows = self.read_services()
        have_bases = [_svc_base(r.code) for r in rows if r.code]
        need_full = [_norm(x.get("code")).upper() for x in (expected or []) if _norm(x.get("code"))]
        need_bases = [_svc_base(x) for x in need_full]
        need_set = set(need_bases)
        have_set = set(have_bases)
        missing = sorted([b for b in need_set if b not in have_set])
        extra = sorted([b for b in have_set if b and b not in need_set])
        # duplicates among bases
        dup = sorted([b for b in have_set if have_bases.count(b) > 1])
        return {
            "need": sorted(need_set),
            "have": sorted(have_set),
            "missing": missing,
            "extra": extra,
            "duplicates": dup,
            "n_rows": len(rows),
        }

    def list_service_indices(self) -> list[int]:
        # В DOM есть инпуты с id combobox-service-<i>
        ids = self.page.locator("[id^='combobox-service-'], [id*='combobox-service-']").all()
        idxs: set[int] = set()
        for loc in ids:
            v = loc.get_attribute("id") or ""
            m = re.search(r"combobox-service-(\d+)$", v)
            if m:
                idxs.add(int(m.group(1)))
        return sorted(idxs)

    def _find_empty_service_row_index(self) -> int | None:
        for i in self.list_service_indices():
            if not _norm(self._read_code(i)):
                return i
        return None

    def wait_for_empty_service_row(self, timeout_ms: int = 60_000) -> int:
        """Ждёт, пока в блоке услуг появится пустая строка (после ручного или авто-клика '+')."""
        deadline = time.time() + (max(0, int(timeout_ms)) / 1000.0)
        while time.time() < deadline:
            i = self._find_empty_service_row_index()
            if i is not None:
                return i
            time.sleep(0.2)
        raise TimeoutError("Не дождались пустой строки услуги (нажмите '+' в блоке «Услуги»).")

    def _services_root(self):
        # Надёжнее всего привязаться к реальным инпутам услуг
        inp0 = self.page.locator("[id^='combobox-service-']").first
        if inp0.count():
            root = inp0.locator("xpath=ancestor::div[contains(@class,'jss421')][1]")
            if root.count():
                return root.first
        loc = self.page.locator("div.jss421").first
        return loc.first if loc.count() else self.page.locator("body")

    def ensure_empty_service_row(self, timeout_ms: int = 30_000) -> int:
        """Гарантирует наличие пустой строки услуги (верхняя строка)."""
        empty = self._find_empty_service_row_index()
        if empty is not None:
            return empty
        self._create_new_service_row(timeout_ms=timeout_ms)
        return self.wait_for_empty_service_row(timeout_ms=timeout_ms)

    def _create_new_service_row(self, timeout_ms: int = 30_000) -> None:
        """Создаёт новую строку услуги: через #add-service или строчный '+' (если шапка disabled)."""
        add_btn = self.page.locator("#add-service").first
        try:
            expect(add_btn).to_be_visible(timeout=timeout_ms)
        except Exception:
            pass

        try:
            if add_btn.count() and add_btn.is_enabled():
                add_btn.click(timeout=5_000)
                return
        except Exception:
            pass

        # fallback: строчный '+' в любой существующей строке (обычно справа от врача)
        idxs = self.list_service_indices()
        if not idxs:
            # если нет строк — всё равно пробуем кликнуть шапку форсом
            try:
                add_btn.click(force=True)
                return
            except Exception as e:
                raise TimeoutError("Не удалось создать строку услуги: нет строк и #add-service disabled") from e

        # берём последнюю заполненную строку
        for i in sorted(idxs, reverse=True):
            if _norm(self._read_code(i)):
                self.click_row_plus(i, timeout_ms=timeout_ms)
                return
        # если все пустые — попробуем первую
        self.click_row_plus(idxs[0], timeout_ms=timeout_ms)

    def click_row_plus(self, i: int, timeout_ms: int = 30_000) -> None:
        """Нажимает '+' внутри конкретной строки услуги (не шапка)."""
        inp = self.page.locator(f"#combobox-service-{i}").first
        row = inp.locator("xpath=ancestor::div[contains(@class,'jss424')][1]").first
        btn = row.locator("button[aria-label=add]:not([disabled]):not(#add-service)").first
        if btn.count() == 0:
            # ждём, что станет доступной
            btn = row.locator("button[aria-label=add]:not(#add-service)").first
            expect(btn).to_be_enabled(timeout=timeout_ms)
        try:
            btn.click(timeout=5_000)
        except Exception:
            btn.click(force=True)

    def _read_code(self, i: int) -> str:
        # Реальное выбранное значение лежит в соседнем блоке react-select как текст.
        # Сам input обычно пустой; поэтому читаем ближайший .Selected-item или Select-value.
        inp = self.page.locator(f"#combobox-service-{i}")
        wrap = inp.locator("xpath=ancestor::div[contains(@class,'Select-control')]")
        label = wrap.locator(".Selected-item").first
        if label.count() == 0:
            label = wrap.locator(".Select-value").first
        try:
            raw_txt = label.inner_text(timeout=1_000) if label.count() else ""
        except Exception:
            raw_txt = ""
        txt = _norm(raw_txt)
        m = _SVC_ANY_RE.search(txt)
        return m.group(1).upper() if m else txt

    def _read_doctor(self, i: int) -> str:
        inp = self.page.locator(f"#doctor-service-{i}").first
        if inp.count() == 0:
            return ""
        wrap = inp.locator("xpath=ancestor::div[contains(@class,'Select-control')]").first
        label = wrap.locator(".Selected-item").first
        if label.count() == 0:
            label = wrap.locator(".Select-value").first
        txt = ""
        if label.count():
            try:
                txt = _norm(label.inner_text(timeout=1_000))
            except Exception:
                txt = ""
        if txt:
            return txt
        # fallback: disabled select часто хранит значение только в title
        try:
            title = _norm(wrap.locator(".Select-value").first.get_attribute("title", timeout=800) or "")
            return title
        except Exception:
            return ""

    def read_services(self) -> list[UiServiceRow]:
        rows: list[UiServiceRow] = []
        for i in self.list_service_indices():
            code = self._read_code(i)
            b = self.page.locator(f"#begin-date-service-{i}").first
            e = self.page.locator(f"#end-date-service-{i}").first
            q = self.page.locator(f"#amount-service-{i}").first
            begin = _norm(b.input_value(timeout=1_000) if b.count() else "")
            end = _norm(e.input_value(timeout=1_000) if e.count() else "")
            qty = _norm(q.input_value(timeout=1_000) if q.count() else "")
            doctor = self._read_doctor(i)
            rows.append(
                UiServiceRow(index=i, code=code, begin_date=begin, end_date=end, qty=qty, doctor=doctor)
            )
        return rows

    def _default_doctor_text(self) -> str:
        for i in self.list_service_indices():
            d = self._read_doctor(i)
            if d:
                return d
        return ""

    def _default_doctor_id(self) -> str:
        """Пытается извлечь табельный/код врача из title выбранного врача."""
        for i in self.list_service_indices():
            # В заполненной строке поле врача может быть disabled и без input#doctor-service-*
            svc_inp = self.page.locator(f"#combobox-service-{i}").first
            row = svc_inp.locator("xpath=ancestor::div[contains(@class,'jss424')][1]").first
            # 1) По тексту Selected-item (у врача начинается с цифр 00136001)
            for el in row.locator(".Selected-item").all():
                txt = _norm(el.inner_text() or "")
                m = re.search(r"\\b(\\d{5,})\\b", txt)
                if m:
                    return m.group(1)
            # 2) fallback: title у Select-value
            for el in row.locator("div.Select-value[title]").all():
                title = _norm(el.get_attribute("title") or "")
                m = re.search(r"\\b(\\d{5,})\\b", title)
                if m:
                    return m.group(1)
        # fallback: берём любой выбранный элемент на странице, начинающийся с табельного
        for el in self.page.locator(".Selected-item").all():
            txt = _norm(el.inner_text() or "")
            m = re.search(r"\\b(\\d{5,})\\b", txt)
            if m:
                return m.group(1)
        return ""

    def set_doctor(self, i: int, doctor_text: str) -> None:
        doc = _norm(doctor_text)
        if not doc:
            return
        inp = self.page.locator(f"#doctor-service-{i}").first
        if inp.count() == 0:
            return
        inp.scroll_into_view_if_needed()
        wrap = inp.locator("xpath=ancestor::div[contains(@class,'Select-control')]").first
        try:
            wrap.click(timeout=3_000)
        except Exception:
            inp.click(force=True)
        inp.fill("")
        # Самый стабильный ввод: табельный/код врача (если есть), иначе первый токен текста
        m = re.match(r"^(\\d{5,})\\b", doc)
        token = m.group(1) if m else doc.split()[0]
        inp.type(token, delay=30)
        # В этом UI подсказки врача рисуются не как Select-option (часто как tooltip).
        # Самый надёжный способ: ArrowDown → Enter → blur (Tab).
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("Enter")
        self.page.keyboard.press("Tab")
        deadline = time.time() + 10.0
        while time.time() < deadline:
            if self._read_doctor(i):
                return
            time.sleep(0.2)

    def wait_row_valid(self, i: int, timeout_ms: int = 30_000) -> None:
        """Ждёт, что строка услуг валидна: нет aria-invalid на датах и врач выбран."""
        t0 = time.time()
        deadline = t0 + (max(0, int(timeout_ms)) / 1000.0)
        b = self.page.locator(f"#begin-date-service-{i}").first
        e = self.page.locator(f"#end-date-service-{i}").first
        while time.time() < deadline:
            ok = True
            try:
                if _norm(b.get_attribute("aria-invalid")) == "true":
                    ok = False
                if _norm(e.get_attribute("aria-invalid")) == "true":
                    ok = False
            except Exception:
                ok = False
            if not _norm(self._read_code(i)):
                ok = False
            if not _norm(self._read_doctor(i)):
                ok = False
            if ok:
                return
            time.sleep(0.2)
        # diagnostics
        try:
            diag = {
                "row": i,
                "code": _norm(self._read_code(i)),
                "doctor": _norm(self._read_doctor(i)),
                "begin": _norm(b.input_value() if b.count() else ""),
                "end": _norm(e.input_value() if e.count() else ""),
                "begin_invalid": _norm(b.get_attribute("aria-invalid") if b.count() else ""),
                "end_invalid": _norm(e.get_attribute("aria-invalid") if e.count() else ""),
            }
        except Exception:
            diag = {"row": i}
        raise TimeoutError(f"Строка услуги не стала валидной (проверьте даты/врача). diag={diag}")

    def cleanup_empty_service_rows(self) -> dict:
        """Удаляет пустые строки услуг (без выбранного кода), чтобы сохранение не блокировалось."""
        removed: list[int] = []
        for i in list(self.list_service_indices()):
            code = _norm(self._read_code(i))
            if code:
                continue
            # Пытаемся нажать "X" (Удалить сведение) в строке
            inp = self.page.locator(f"#combobox-service-{i}").first
            btn = inp.locator(
                "xpath=ancestor::div[contains(@class,'jss424')][1]//button[@title='Удалить сведение']"
            ).first
            if btn.count() == 0:
                btn = inp.locator(
                    "xpath=ancestor::div[contains(@class,'jss424')][1]//button[contains(@title,'Удал')]"
                ).first
            if btn.count():
                try:
                    btn.click(timeout=2_000)
                except Exception:
                    try:
                        btn.click(force=True)
                    except Exception:
                        continue
                removed.append(i)
        return {"removed": removed, "removed_n": len(removed)}

    def delete_service_row(self, i: int) -> bool:
        """Удаляет строку услуги по индексу (кнопка X)."""
        before_n = self.page.locator("[id^='combobox-service-']").count()
        inp = self.page.locator(f"#combobox-service-{i}").first
        if inp.count() == 0:
            return False
        btn = inp.locator(
            "xpath=ancestor::div[contains(@class,'jss424')][1]//button[@title='Удалить сведение']"
        ).first
        if btn.count() == 0:
            btn = inp.locator(
                "xpath=ancestor::div[contains(@class,'jss424')][1]//button[contains(@title,'Удал')]"
            ).first
        if btn.count() == 0:
            return False
        try:
            btn.click(timeout=3_000)
        except Exception:
            btn.click(force=True)
        # ждём, что число строк уменьшилось или текущий инпут исчез
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if self.page.locator(f"#combobox-service-{i}").count() == 0:
                return True
            if self.page.locator("[id^='combobox-service-']").count() < before_n:
                return True
            time.sleep(0.1)
        return False

    def delete_service_by_base(self, base_code: str) -> bool:
        """Удаляет одну строку услуги по base-коду (Axx.xx.xxx / Bxx.xx.xxx).

        Надёжнее индекса: после удалений UI переиндексируется.
        """
        b = _svc_base(_norm(base_code))
        if not b:
            return False
        hit = self.page.locator(f"text={b}").first
        if hit.count() == 0:
            return False
        row = hit.locator("xpath=ancestor::div[contains(@class,'jss424')][1]").first
        btn = row.locator("button[title='Удалить сведение']").first
        if btn.count() == 0:
            btn = row.locator("button[title*='Удал']").first
        if btn.count() == 0:
            return False
        try:
            btn.click(timeout=3_000)
        except Exception:
            btn.click(force=True)
        deadline = time.time() + 6.0
        while time.time() < deadline:
            try:
                cur = self.read_services()
                have_b = {_svc_base(r.code) for r in cur if r.code}
                if b not in have_b:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def apply_expected_sync(self, expected: list[dict], *, doctor_id: str = "") -> dict:
        """SYNC: привести услуги к точному набору expected (удалить лишние и дубли)."""
        doctor_id = _norm(doctor_id)
        default_doctor = doctor_id or self._default_doctor_id() or self._default_doctor_text()

        # нормализуем ожидаемый набор по base-кодам
        exp_items = []
        for x in expected or []:
            code = _norm(x.get("code"))
            if not code:
                continue
            exp_items.append(
                {
                    "code": code.upper(),
                    "base": _svc_base(code),
                    "begin": _norm(x.get("begin_date")),
                    "end": _norm(x.get("end_date")),
                    "qty": _norm(x.get("qty")) or "1",
                }
            )
        exp_bases = {e["base"] for e in exp_items}

        deleted: list[dict] = []
        # 1) удалить всё, что не в expected (по base-коду, чтобы не ломаться от переиндексации)
        guard = 0
        while True:
            guard += 1
            if guard > 25:
                break
            current = self.read_services()
            extras = []
            for r in current:
                b = _svc_base(r.code)
                if b and b not in exp_bases:
                    extras.append((b, r))
            if not extras:
                break
            b, r = extras[0]
            ok = self.delete_service_by_base(b) or self.delete_service_row(r.index)
            if ok:
                deleted.append({"op": "delete", "base": b, "code": r.code, "row": r.index})
            else:
                break
        current = self.read_services()

        # 2) удалить дубли по expected base (оставить по одной)
        by_base: dict[str, list[UiServiceRow]] = {}
        for r in current:
            b = _svc_base(r.code)
            if b:
                by_base.setdefault(b, []).append(r)
        for b, rows in by_base.items():
            if b in exp_bases and len(rows) > 1:
                # удаляем "хвост" по индексу (оставляем минимальный индекс)
                rows_sorted = sorted(rows, key=lambda x: x.index)
                for r in rows_sorted[1:]:
                    ok = self.delete_service_by_base(b) or self.delete_service_row(r.index)
                    if ok:
                        deleted.append({"op": "dedupe_delete", "base": b, "code": r.code, "row": r.index})
        current = self.read_services()

        actions: list[dict] = []
        # 3) для каждого expected обеспечить ровно одну строку (добавить если нет)
        for e in exp_items:
            # если после чистки нет ни одной строки — добавим
            current = self.read_services()
            by_base = {}
            for r in current:
                by_base.setdefault(_svc_base(r.code), []).append(r)
            rows = by_base.get(e["base"], [])
            if not rows:
                i = self.ensure_empty_service_row()
                self.select_service_by_code(i, e["code"])
                # после выбора переиндексация — ищем строку по base
                current = self.read_services()
                rows2 = [r for r in current if _svc_base(r.code) == e["base"]]
                i2 = rows2[0].index if rows2 else i
                self.set_dates_qty(i2, e["begin"], e["end"], e["qty"])
                if default_doctor:
                    self.set_doctor(i2, default_doctor)
                self.wait_row_valid(i2, timeout_ms=30_000)
                actions.append({"op": "add", "code": e["code"], "row": i2})
                current = self.read_services()
                by_base = {_svc_base(r.code): [r] for r in current if r.code}
                rows = [r for r in current if _svc_base(r.code) == e["base"]]
            # оставить первую строку, остальные удалить
            if not rows:
                # UI мог переиндексировать/скрыть инпуты; используем i2 как keep
                keep = UiServiceRow(index=i2, code=e["code"], begin_date=e["begin"], end_date=e["end"], qty=e["qty"])
            else:
                keep = rows[0]
            for r in rows[1:]:
                if self.delete_service_row(r.index):
                    deleted.append({"op": "dedupe_delete", "code": r.code, "row": r.index})
            # привести keep к нужным полям
            self.set_dates_qty(keep.index, e["begin"] or keep.begin_date, e["end"] or keep.end_date, e["qty"] or keep.qty)
            if default_doctor and not _norm(keep.doctor):
                self.set_doctor(keep.index, default_doctor)
            actions.append({"op": "ensure", "code": e["code"], "row": keep.index})

        # 3) подчистить пустые строки
        cleanup = self.cleanup_empty_service_rows()
        return {"actions": actions, "deleted": deleted, "cleanup": cleanup}

    def add_empty_row(self) -> int:
        return self.ensure_empty_service_row()

    def set_dates_qty(self, i: int, begin_date: str, end_date: str, qty: str) -> None:
        self.page.locator(f"#begin-date-service-{i}").fill(_to_ui_date(str(begin_date)))
        self.page.locator(f"#end-date-service-{i}").fill(_to_ui_date(str(end_date)))
        self.page.locator(f"#amount-service-{i}").fill(str(qty))

    def select_service_by_code(self, i: int, code: str) -> None:
        # react-select: кликаем в input, печатаем код, выбираем точное совпадение если есть,
        # иначе — первый результат (ArrowDown+Enter).
        inp = self.page.locator(f"#combobox-service-{i}").first
        inp.scroll_into_view_if_needed()
        # Клик по контейнеру, чтобы не ловить "intercepts pointer events"
        wrap = inp.locator("xpath=ancestor::div[contains(@class,'Select-control')]").first
        want = str(code or "").strip().upper()
        if not want:
            return

        def _open_and_type() -> None:
            try:
                wrap.click(timeout=3_000)
            except Exception:
                inp.click(force=True)
            inp.fill("")
            inp.type(want, delay=30)

        def _try_pick_exact() -> bool:
            # react-select обычно рисует меню глобально, но чаще всего рядом с контролом
            menu = self.page.locator("div.Select-menu-outer").last
            opts = menu.locator("div.Select-option")
            # fallback для других разметок
            if opts.count() == 0:
                opts = self.page.locator("[role='option']")
            # ждём, что опции появятся
            deadline = time.time() + 3.0
            while time.time() < deadline:
                if opts.count() > 0:
                    break
                time.sleep(0.1)
            if opts.count() == 0:
                return False

            # Выбираем опцию, где извлечённый код строго равен want.
            # Это защищает от случая, когда want является префиксом want.001
            n = min(int(opts.count()), 30)
            for j in range(n):
                opt = opts.nth(j)
                try:
                    txt = _norm(opt.inner_text(timeout=500)).upper()
                except Exception:
                    txt = ""
                if not txt:
                    continue
                m = _SVC_ANY_RE.search(txt)
                if not m:
                    continue
                found = m.group(1).upper()
                if found == want:
                    try:
                        opt.click(timeout=2_000)
                    except Exception:
                        opt.click(force=True)
                    return True
            return False

        def _pick_first() -> None:
            self.page.keyboard.press("ArrowDown")
            self.page.keyboard.press("Enter")

        # 2 попытки: сначала пытаемся кликнуть точное совпадение, иначе fallback
        for attempt in range(2):
            _open_and_type()
            picked = _try_pick_exact()
            if not picked:
                _pick_first()
            # ждём, что код реально появился в строке
            deadline = time.time() + 10.0
            while time.time() < deadline:
                cur = _norm(self._read_code(i)).upper()
                if not cur:
                    time.sleep(0.2)
                    continue
                # если хотели базовый код (без хвоста .xxx), добиваемся точного выбора
                if want.count(".") == 2:
                    if cur == want:
                        return
                    # если выбрался хвост .xxx — попробуем ещё раз подобрать точное (если есть)
                    break
                else:
                    if cur.startswith(want):
                        return
                time.sleep(0.2)
        # как минимум что-то выбралось; дальше пайплайн проверит совпадение в sync
        return

    def apply_expected_add_update(self, expected: list[dict], *, doctor_id: str = "") -> dict:
        """MVP: добавить отсутствующие, поправить даты/qty для существующих по коду."""
        doctor_id = _norm(doctor_id)
        default_doctor = doctor_id or self._default_doctor_id() or self._default_doctor_text()
        current = self.read_services()
        by_code: dict[str, UiServiceRow] = {r.code: r for r in current if r.code}
        by_base: dict[str, UiServiceRow] = {_svc_base(r.code): r for r in current if r.code}

        actions: list[dict] = []
        to_add: list[dict] = []
        for exp in expected:
            code = _norm(exp.get("code"))
            if not code:
                continue
            begin = _norm(exp.get("begin_date"))
            end = _norm(exp.get("end_date"))
            qty = _norm(exp.get("qty"))
            base = _svc_base(code)
            if code in by_code or base in by_base:
                r = by_code.get(code) or by_base[base]
                if (begin and begin != r.begin_date) or (end and end != r.end_date) or (qty and qty != r.qty):
                    self.set_dates_qty(r.index, begin or r.begin_date, end or r.end_date, qty or r.qty)
                # если врач пустой — проставим по умолчанию
                if default_doctor and not _norm(r.doctor):
                    self.set_doctor(r.index, default_doctor)
                    actions.append({"op": "update", "code": code, "row": r.index})
            else:
                to_add.append({"code": code, "begin": begin, "end": end, "qty": qty or "1"})

        # Добавляем детерминированно: заполняем верхнюю пустую строку → жмём '+' в этой же строке
        for k, item in enumerate(to_add):
            empty_i = self.ensure_empty_service_row()
            code = item["code"]
            self.select_service_by_code(empty_i, code)
            # После выбора react-select может переиндексировать строки — переопределяем индекс по коду.
            current = self.read_services()
            by_code = {r.code: r for r in current if r.code}
            by_base = {_svc_base(r.code): r for r in current if r.code}
            i2 = by_code.get(code).index if code in by_code else empty_i

            self.set_dates_qty(i2, item["begin"], item["end"], item["qty"])
            if default_doctor:
                self.set_doctor(i2, default_doctor)
            self.wait_row_valid(i2, timeout_ms=30_000)
            actions.append({"op": "add", "code": code, "row": i2})

            # перечитать DOM (после выбора/вставки UI может переиндексировать)
            current = self.read_services()
            by_code = {r.code: r for r in current if r.code}

            # Следующую строку создадим на следующей итерации через ensure_empty_service_row()

        return {"actions": actions, "before_n": len(current), "after_n": len(self.list_service_indices())}


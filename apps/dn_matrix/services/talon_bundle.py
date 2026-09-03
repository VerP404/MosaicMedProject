"""Генерация пакета талонов ДН (шапка + услуги) — те же 2 Excel, что в портале."""

from __future__ import annotations

import io
import random
import re
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from openpyxl import Workbook

from apps.dn_matrix.models import MatrixEdition
from apps.dn_matrix.services.batch_pick import parse_mkb_list, resolve_specialty_id
from apps.dn_matrix.services.matrix import (
    MatrixPickCache,
    build_matrix_pick_cache,
    cap_doctor_visits,
    category_for_mkb_in_cache,
    normalize_mkb,
    select_services_from_cache,
)
from apps.dn_matrix.services.pick_pricing import is_per_visit_service
from apps.dn_matrix.services.rf_workdays import pick_visit_dates, pick_visit_dates_from_anchor

_DOCTOR_ID_RE = re.compile(r"\b(\d{5,})\b")
_ENP_DIGITS = re.compile(r"\D+")


def talon_bundle_export_stamp(when: datetime | None = None) -> str:
    from django.utils import timezone

    dt = when or timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return timezone.localtime(dt).strftime("%Y-%m-%d_%H%M%S")


def talon_bundle_excel_names(stamp: str | None = None) -> tuple[str, str, str]:
    suffix = stamp or talon_bundle_export_stamp()
    return suffix, f"талоны_{suffix}.xlsx", f"услуги_{suffix}.xlsx"


TALON_HEADER_COLUMNS_BASE = [
    "Талон",
    "начало",
    "окончание",
    "ЕНП",
    "врач",
    "Корпус",
    "цель",
    "случай",
    "случай_2",
    "посещений в МО",
    "Диагноз",
    "Диагноз 2",
    "Категория",
    "ДИСП. НАБЛ",
    "тип",
    "результат",
    "исход",
    "характер",
    "напр номер",
    "напр дата",
    "напр орган",
    "напр дано",
    "Соцстатус",
    "Вид занятости",
]

TALON_HEADER_COLUMNS_ONCOLOGY = [
    "Цель консил",
    "Повод",
    "дополнительное направление организация",
    "дополнительное направление дата",
    "дополнительное направление вид",
]

SERVICE_COLUMNS = [
    "Талон",
    "Код услуги",
    "Дата начала",
    "Дата окончания",
    "Кол-во",
    "Врач",
]

DEFAULT_HEADER_DEFAULTS: dict[str, str] = {
    "цель": "3",
    "случай": "Первичный",
    "случай_2": "Законченный",
    "посещений в МО": "3",
    "ДИСП. НАБЛ": "1",
    "тип": "3",
    "результат": "301",
    "исход": "304",
    "характер": "3",
    "напр номер": "бн",
    "напр орган": "360025",
    "напр дано": "Амбулаторно",
    "Корпус": "",
    "врач": "",
}


@dataclass
class TalonBundleItem:
    enp: str
    ds1: str
    ds2_list: list[str] = field(default_factory=list)
    specialty: str | None = None
    doctor_id: str | None = None
    corpus: str | None = None
    diagnosis_category_code: str | None = None
    category_168n: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    birth_date: date | None = None
    journal_visit_date: date | None = None
    blocked_dates: tuple[date, ...] = field(default_factory=tuple)


@dataclass
class TalonBundleParams:
    date_from: date
    date_to: date
    visit_step: int = 1
    visits: int = 3
    edition: MatrixEdition | None = None
    header_defaults: dict[str, str] = field(default_factory=dict)
    seed: int | None = None


def norm_enp(raw: str | None) -> str:
    return _ENP_DIGITS.sub("", str(raw or ""))


def codes_from_birth_year(birth: date | None, *, today: date | None = None) -> tuple[str, str]:
    """Соцстатус и вид занятости: возраст = текущий год − год рождения."""
    if not birth:
        return "", ""
    age = (today or date.today()).year - birth.year
    if age > 60:
        return "22", "3"
    return "11", "1"


def fill_missing_birth_dates(items: list[TalonBundleItem]) -> int:
    """Подставляет ДР из dn_app_person, если в строке её нет."""
    need = [it for it in items if it.birth_date is None and norm_enp(it.enp)]
    enps = list({norm_enp(it.enp) for it in need})
    if not enps:
        return 0
    from apps.dn_app.models import Person

    found: dict[str, date] = {}
    for i in range(0, len(enps), 1000):
        chunk = enps[i : i + 1000]
        for enp, dr in Person.objects.filter(enp__in=chunk).exclude(dr__isnull=True).values_list("enp", "dr"):
            key = norm_enp(enp)
            if key and dr:
                found[key] = dr
    filled = 0
    for it in need:
        dr = found.get(norm_enp(it.enp))
        if dr:
            it.birth_date = dr
            filled += 1
    return filled


def extract_doctor_id(text: str | None) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    m = _DOCTOR_ID_RE.search(s)
    if m:
        return m.group(1)
    compact = s.replace(" ", "")
    if compact.isdigit() and len(compact) >= 5:
        return compact
    return ""


def _merge_header_defaults(raw: dict[str, str] | None) -> dict[str, str]:
    merged = dict(DEFAULT_HEADER_DEFAULTS)
    if raw:
        for key, val in raw.items():
            if val is not None:
                merged[str(key)] = str(val).strip()
    return merged


def _is_oncology_row(*, specialty: str | None, category_code: str | None, category_title: str | None) -> bool:
    title = (category_title or "").strip().upper()
    if title == "ОНКО" or category_code == "ct_2":
        return True
    spec = (specialty or "").lower().replace("ё", "е")
    return "онколог" in spec


def _build_service_rows(
    *,
    plan_id: int,
    services: list[dict],
    visit_dates: list[str],
    doctor_id: str,
    visits: int,
) -> list[dict[str, str]]:
    """Приём врача — первая строка, период начало–окончание, qty=явки; остальное — 1-я дата, qty=1."""
    if not visit_dates:
        return []
    rows: list[dict[str, str]] = []
    first_date = visit_dates[0]
    last_date = visit_dates[-1]
    qty_visits = str(max(1, int(visits)))

    usable = [svc for svc in services if not svc.get("unavailable")]
    per_visit = [svc for svc in usable if is_per_visit_service(str(svc.get("title") or ""))]
    other = [svc for svc in usable if not is_per_visit_service(str(svc.get("title") or ""))]

    for svc in per_visit:
        code = str(svc.get("code") or "").strip().upper()
        if not code:
            continue
        rows.append(
            {
                "Талон": str(plan_id),
                "Код услуги": code,
                "Дата начала": first_date,
                "Дата окончания": last_date,
                "Кол-во": qty_visits,
                "Врач": doctor_id,
            }
        )

    for svc in other:
        code = str(svc.get("code") or "").strip().upper()
        if not code:
            continue
        rows.append(
            {
                "Талон": str(plan_id),
                "Код услуги": code,
                "Дата начала": first_date,
                "Дата окончания": first_date,
                "Кол-во": "1",
                "Врач": doctor_id,
            }
        )

    return rows


def _pick_dates_with_shrink(
    date_from: date,
    date_to: date,
    *,
    visits: int,
    visit_step: int,
    rng,
) -> tuple[list[str], int]:
    last_error = ""
    for n in range(max(1, int(visits)), 0, -1):
        try:
            dates = pick_visit_dates(
                date_from,
                date_to,
                visits=n,
                step_workdays=visit_step,
                rng=rng,
            )
            return dates, n
        except ValueError as exc:
            last_error = str(exc)
    raise ValueError(last_error or "Не удалось подобрать даты явок.")


def _parse_visit_ui_date(text: str) -> date | None:
    try:
        return datetime.strptime(str(text)[:8], "%d-%m-%y").date()
    except ValueError:
        return None


def _pick_dates_from_journal(
    item: TalonBundleItem,
    *,
    visits: int,
    visit_step: int,
    extra_blocked: set[date] | None = None,
) -> tuple[list[str], int]:
    last_error = ""
    blocked = set(item.blocked_dates or ())
    if extra_blocked:
        blocked |= set(extra_blocked)
    for n in range(max(1, int(visits)), 0, -1):
        try:
            dates = pick_visit_dates_from_anchor(
                item.journal_visit_date,
                visits=n,
                step_workdays=visit_step,
                offset_workdays=5,
                blocked=blocked,
            )
            return dates, n
        except ValueError as exc:
            last_error = str(exc)
    raise ValueError(last_error or "Не удалось подобрать даты явок по журналу.")


def build_talon_bundle(
    *,
    items: list[TalonBundleItem],
    params: TalonBundleParams,
) -> dict[str, Any]:
    warnings: list[str] = []
    headers_out: list[dict[str, str]] = []
    services_out: list[dict[str, str]] = []

    if not params.edition:
        raise ValueError("Нужна редакция матрицы.")

    edition = params.edition
    pick_cache: MatrixPickCache = build_matrix_pick_cache(edition)
    specialties = list(edition.specialties.all().order_by("sort_order", "id"))
    hdr_defaults = _merge_header_defaults(params.header_defaults)
    default_doctor = extract_doctor_id(hdr_defaults.get("врач", "")) or str(hdr_defaults.get("врач") or "").strip()
    default_corpus = hdr_defaults.get("Корпус", "")
    max_visits = cap_doctor_visits(edition, params.visits)
    visit_step = 2 if int(params.visit_step) == 2 else 1

    rng = random.Random(params.seed)
    plan_id = 0
    skipped_no_enp = 0
    skipped_no_specialty = 0
    missing_dr = 0
    spec_memo: dict[tuple[str, str], int | None] = {}
    used_visit_dates: dict[str, set[date]] = {}
    fill_missing_birth_dates(items)

    price_on = params.date_to

    for item in items:
        enp = norm_enp(item.enp)
        if not enp:
            skipped_no_enp += 1
            continue

        ds1 = normalize_mkb(item.ds1 or "")
        if not ds1:
            warnings.append(f"ЕНП {enp}: пустой основной диагноз, строка пропущена.")
            continue

        profile = (item.specialty or "").strip()
        spec_key = (profile, ds1)
        if spec_key not in spec_memo:
            spec_memo[spec_key] = resolve_specialty_id(pick_cache, specialties, profile=profile, mkb_code=ds1)
        specialty_id = spec_memo[spec_key]
        if specialty_id is None:
            skipped_no_specialty += 1
            warnings.append(f"ЕНП {enp}: специальность не сопоставлена с матрицей ({profile or 'без профиля'}).")
            continue

        spec_title = next((s.title for s in specialties if s.id == specialty_id), profile)
        row_from = item.date_from or params.date_from
        row_to = item.date_to or params.date_to
        if row_to < row_from:
            warnings.append(f"ЕНП {enp}: дата окончания раньше начала, строка пропущена.")
            continue

        try:
            if item.journal_visit_date:
                visit_dates, used_visits = _pick_dates_from_journal(
                    item,
                    visits=max_visits,
                    visit_step=visit_step,
                    extra_blocked=used_visit_dates.get(enp),
                )
            else:
                visit_dates, used_visits = _pick_dates_with_shrink(
                    row_from,
                    row_to,
                    visits=max_visits,
                    visit_step=visit_step,
                    rng=rng,
                )
        except ValueError as exc:
            warnings.append(f"ЕНП {enp}: {exc}")
            continue
        if used_visits < max_visits:
            warnings.append(f"ЕНП {enp}: явок уменьшено до {used_visits} — не хватает рабочих дней в интервале.")

        price_on = item.date_to or params.date_to
        services, _, _ = select_services_from_cache(
            pick_cache,
            specialty_id=specialty_id,
            mkb_code=ds1,
            price_on=price_on,
            secondary_mkb_list=item.ds2_list or None,
        )
        included = [svc for svc in services if not svc.get("unavailable")]
        if not included:
            warnings.append(f"ЕНП {enp}: матрица не вернула проводимых услуг для {ds1}.")
            continue

        plan_id += 1
        if item.journal_visit_date:
            used = used_visit_dates.setdefault(enp, set())
            for raw in visit_dates:
                parsed = _parse_visit_ui_date(raw)
                if parsed:
                    used.add(parsed)
        doctor_id = extract_doctor_id(item.doctor_id) or (item.doctor_id or "").strip() or default_doctor
        corpus = (item.corpus or "").strip() or default_corpus

        cat = category_for_mkb_in_cache(pick_cache, ds1)
        category_code = item.diagnosis_category_code or (cat[0] if cat else None)
        category_title = (cat[1] if cat else "") or (item.category_168n or "")

        social, employment = codes_from_birth_year(item.birth_date)
        if not social:
            missing_dr += 1

        row: dict[str, str] = {
            "Талон": str(plan_id),
            "начало": visit_dates[0],
            "окончание": visit_dates[-1],
            "ЕНП": enp,
            "врач": doctor_id,
            "Корпус": corpus,
            "Диагноз": ds1,
            "Диагноз 2": ", ".join(normalize_mkb(x) for x in (item.ds2_list or []) if normalize_mkb(x)),
            "Категория": category_title,
            "напр дата": visit_dates[0],
            "посещений в МО": str(used_visits),
            "Соцстатус": social,
            "Вид занятости": employment,
        }
        for key in (
            "цель",
            "случай",
            "случай_2",
            "ДИСП. НАБЛ",
            "тип",
            "результат",
            "исход",
            "характер",
            "напр номер",
            "напр орган",
            "напр дано",
        ):
            row[key] = hdr_defaults.get(key, "")

        if _is_oncology_row(specialty=spec_title, category_code=category_code, category_title=category_title):
            row["Цель консил"] = "0"
            row["Повод"] = "3"
            row["дополнительное направление организация"] = hdr_defaults.get("напр орган", "360025")
            row["дополнительное направление дата"] = visit_dates[0]
            row["дополнительное направление вид"] = "Направление к онкологу"

        headers_out.append(row)
        services_out.extend(
            _build_service_rows(
                plan_id=plan_id,
                services=services,
                visit_dates=visit_dates,
                doctor_id=doctor_id,
                visits=used_visits,
            )
        )

    if skipped_no_enp:
        warnings.append(f"Пропущено строк без ЕНП: {skipped_no_enp}.")
    if skipped_no_specialty:
        warnings.append(f"Пропущено строк без сопоставленной специальности: {skipped_no_specialty}.")
    if missing_dr:
        warnings.append(
            f"Нет даты рождения у {missing_dr} строк — Соцстатус и вид занятости не заполнены."
        )

    return {
        "headers": headers_out,
        "services": services_out,
        "warnings": warnings,
        "talons_count": len(headers_out),
        "services_count": len(services_out),
    }


def _write_sheet(wb: Workbook, title: str, columns: list[str], rows: list[dict[str, str]]) -> None:
    ws = wb.active
    ws.title = title
    ws.append(columns)
    for row in rows:
        ws.append([row.get(col, "") for col in columns])


def render_talon_bundle_xlsx(
    *,
    headers: list[dict[str, str]],
    services: list[dict[str, str]],
) -> tuple[bytes, bytes]:
    header_cols = list(TALON_HEADER_COLUMNS_BASE)
    if any(str(row.get("талон_омс") or "").strip() for row in headers):
        header_cols = ["Талон", "талон_омс"] + [c for c in header_cols if c != "Талон"]
    if any("Цель консил" in row for row in headers):
        header_cols.extend(TALON_HEADER_COLUMNS_ONCOLOGY)

    wb_t = Workbook()
    _write_sheet(wb_t, "талоны", header_cols, headers)
    buf_t = io.BytesIO()
    wb_t.save(buf_t)

    wb_s = Workbook()
    _write_sheet(wb_s, "услуги", SERVICE_COLUMNS, services)
    buf_s = io.BytesIO()
    wb_s.save(buf_s)
    return buf_t.getvalue(), buf_s.getvalue()


def render_talon_bundle_zip(
    *,
    headers: list[dict[str, str]],
    services: list[dict[str, str]],
    stamp: str | None = None,
) -> tuple[bytes, str]:
    talons_xlsx, services_xlsx = render_talon_bundle_xlsx(headers=headers, services=services)
    file_stamp, talons_name, services_name = talon_bundle_excel_names(stamp)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(talons_name, talons_xlsx)
        zf.writestr(services_name, services_xlsx)
    return buf.getvalue(), file_stamp

from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

from playwright.sync_api import Page, expect

from apps.dash_dn.bot_tasks import db as task_db
from apps.dash_dn.claim_bot.browser import open_context
from apps.dash_dn.claim_bot.claim_page import ClaimPage
from apps.dash_dn.claim_bot.settings import load_settings


def _worker_id() -> str:
    return (os.environ.get("CLAIM_BOT_WORKER_ID") or "worker-1").strip()


def _task_artifact_dir(base: Path, task_id: int) -> Path:
    d = base / f"task_{task_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _screenshot(page: Page, path: Path) -> None:
    page.screenshot(path=str(path), full_page=True)


def _looks_like_login(page: Page) -> bool:
    u = (page.url or "").lower()
    if "login" in u or "signin" in u:
        return True
    # эвристика: есть password input и нет add-service
    try:
        if page.locator("input[type='password']").count() and page.locator("#add-service").count() == 0:
            return True
    except Exception:
        return False
    return False


def _login(page: Page, base_root: str, username: str, password: str) -> None:
    page.goto(base_root, wait_until="domcontentloaded")
    # Пытаемся найти поля логина/пароля типовыми способами
    u_locators = [
        "input[name='username']",
        "input[name='login']",
        "input#username",
        "input#login",
        "input[type='text']",
    ]
    p_locators = ["input[name='password']", "input#password", "input[type='password']"]

    u = None
    for sel in u_locators:
        loc = page.locator(sel).first
        if loc.count():
            u = loc
            break
    p = None
    for sel in p_locators:
        loc = page.locator(sel).first
        if loc.count():
            p = loc
            break
    if u is None or p is None:
        raise RuntimeError("Не удалось найти поля логина/пароля на странице входа.")

    u.fill(username)
    p.fill(password)
    # submit
    submit = page.locator("button[type='submit']").first
    if submit.count() == 0:
        submit = page.locator("button:has-text('Войти')").first
    if submit.count() == 0:
        # fallback: Enter в пароле
        page.keyboard.press("Enter")
    else:
        submit.click()

    # ждём, что либо ушли со страницы логина, либо появился признак приложения
    try:
        expect(page.locator("#add-service")).not_to_be_visible(timeout=2_000)
    except Exception:
        pass
    page.wait_for_load_state("domcontentloaded")


def run_once() -> bool:
    """Берёт одну задачу из очереди и выполняет. Возвращает True, если задача была."""
    worker_id = _worker_id()
    try:
        db_path = str(task_db.get_db_path())
    except Exception:
        db_path = "<unknown>"
    print(f"claim-bot: polling queue db={db_path}", flush=True)
    settings = load_settings()
    task = task_db.claim_next_task(worker_id=worker_id)
    if not task:
        return False

    task_id = int(task["id"])
    print(f"claim-bot: claimed task id={task_id} by {worker_id}", flush=True)
    art_dir = _task_artifact_dir(settings.artifacts_dir, task_id)
    storage_state = art_dir / "storage_state.json"

    try:
        payload = json.loads(task.get("payload_json") or "{}")
        talon_id = str(payload.get("talon_id") or task.get("talon_id") or "").strip()
        expected = payload.get("expected_services") or []
        mode = str(payload.get("mode") or "add_update")
        ctx = payload.get("context") or {}
        doctor_id = str(ctx.get("doctor_id") or "").strip()

        if not talon_id:
            raise ValueError("payload.talon_id is empty")

        with open_context(settings, storage_state_path=storage_state) as (_pw, _br, ctx):
            print(
                f"claim-bot: browser started (headless={settings.headless}, slowmo_ms={settings.slowmo_ms}, base_url={settings.base_url})",
                flush=True,
            )
            page = ctx.new_page()
            # tracing для отладки
            ctx.tracing.start(screenshots=True, snapshots=True, sources=False)

            claim = ClaimPage(page, base_url=settings.base_url)
            print(f"claim-bot: opening talon {talon_id} (mode={mode}, doctor_id={doctor_id or 'auto'})", flush=True)
            claim.open_talon(talon_id)
            if _looks_like_login(page):
                # base root: http://host:port/
                root = settings.base_url.split("/claim/")[0].rstrip("/") + "/"
                _login(page, root, settings.username, settings.password)
                claim.open_talon(talon_id)
            claim.wait_ready()

            _screenshot(page, art_dir / "before.png")

            # Режим "ручной плюс": ждём, пока пользователь нажмёт '+' в ЭТОМ окне воркера,
            # чтобы появилась пустая строка в блоке услуг.
            wait_ms_raw = (os.environ.get("CLAIM_BOT_WAIT_EMPTY_ROW_MS") or "").strip()
            try:
                wait_ms = int(wait_ms_raw) if wait_ms_raw else 0
            except ValueError:
                wait_ms = 0
            if wait_ms > 0:
                claim.wait_for_empty_service_row(timeout_ms=wait_ms)

            if mode not in {"add_update", "sync"}:
                raise ValueError(f"Unsupported mode: {mode}")

            if mode == "sync":
                result = claim.apply_expected_sync(expected, doctor_id=doctor_id)
                cleanup = result.get("cleanup") or {}
                strict = claim.verify_exact_set_edit(expected)
                if strict.get("missing") or strict.get("extra") or strict.get("duplicates"):
                    raise RuntimeError(f"SYNC pre-save verify failed: {strict}")
                result["pre_save_verify"] = strict
            else:
                result = claim.apply_expected_add_update(expected, doctor_id=doctor_id)
                cleanup = claim.cleanup_empty_service_rows()
            claim.save()
            _screenshot(page, art_dir / "after_save.png")
            verify = claim.verify_expected_present(expected)
            # жёсткая проверка: перезагрузить талон и ещё раз прочитать
            claim.open_talon(talon_id)
            claim.wait_ready()
            _screenshot(page, art_dir / "after_reload.png")
            # После reload UI может быть в режиме просмотра без combobox-service-*.
            # Пытаемся включить редактирование и дождаться появления строк услуг.
            try:
                claim._ensure_editable(timeout_ms=20_000)  # best-effort
            except Exception:
                pass
            try:
                expect(page.locator("[id^='combobox-service-']").first).to_be_visible(timeout=20_000)
            except Exception:
                pass
            verify2 = claim.verify_expected_present(expected)
            # После reload DOM может не содержать коды услуг; не валим SYNC по этому.
            if mode != "sync" and verify2.get("missing"):
                raise RuntimeError(f"После перезагрузки талона не найдены услуги: {verify2.get('missing')}")

            _screenshot(page, art_dir / "after.png")

            ctx.storage_state(path=str(storage_state))
            ctx.tracing.stop(path=str(art_dir / "trace.zip"))

        task_db.mark_task_succeeded(
            task_id,
            result={
                "talon_id": talon_id,
                "mode": mode,
                "verify": verify,
                "verify_after_reload": verify2,
                "cleanup": cleanup,
                **result,
            },
            artifact_dir=str(art_dir),
        )
        _save_text(art_dir / "run.log", json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
        return True

    except Exception as e:
        tb = traceback.format_exc()
        task_db.mark_task_failed(
            task_id,
            error=str(e),
            result={"traceback": tb},
            artifact_dir=str(art_dir),
        )
        _save_text(art_dir / "run.log", tb)
        return True


def run_forever(poll_seconds: float = 1.5) -> None:
    import time
    import sys

    last_idle_log = 0.0
    try:
        db_path = str(task_db.get_db_path())
    except Exception:
        db_path = "<unknown>"
    print(f"claim-bot: started (py={sys.version.split()[0]}) db={db_path}", flush=True)
    while True:
        has_task = run_once()
        if not has_task:
            now = time.time()
            if now - last_idle_log > 10:
                print("claim-bot: idle, waiting for queued tasks...", flush=True)
                last_idle_log = now
            time.sleep(float(poll_seconds))


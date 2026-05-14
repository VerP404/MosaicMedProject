from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Playwright, sync_playwright

from apps.dash_dn.claim_bot.settings import ClaimBotSettings


def _launch_browser(pw: Playwright, s: ClaimBotSettings) -> Browser:
    btype = getattr(pw, s.browser)
    return btype.launch(headless=bool(s.headless), slow_mo=int(s.slowmo_ms or 0))


@contextmanager
def open_context(
    settings: ClaimBotSettings,
    *,
    storage_state_path: Path | None = None,
) -> tuple[Playwright, Browser, BrowserContext]:
    """Контекст браузера с возможностью reuse сессии через storage_state."""
    with sync_playwright() as pw:
        browser = _launch_browser(pw, settings)
        ctx_kwargs = {}
        if storage_state_path and storage_state_path.exists():
            ctx_kwargs["storage_state"] = str(storage_state_path)
        context = browser.new_context(**ctx_kwargs)
        try:
            yield pw, browser, context
        finally:
            context.close()
            browser.close()


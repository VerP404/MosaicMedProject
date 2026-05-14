from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()


def _maybe_load_dotenv() -> None:
    """Best-effort загрузка переменных из .env для запуска воркера вне Dash."""
    # settings.py → .../apps/dash_dn/claim_bot/settings.py
    # root проекта: .../MosaicMedProject
    root = Path(__file__).resolve().parents[3]
    env_path = root / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            v = v.strip().strip("\"").strip("'")
            if not k or k in os.environ:
                continue
            os.environ[k] = v
    except Exception:
        # не падаем, просто работаем с тем, что есть в окружении
        return


@dataclass(frozen=True)
class ClaimBotSettings:
    base_url: str
    username: str
    password: str
    headless: bool = True
    slowmo_ms: int = 0
    artifacts_dir: Path = Path("artifacts").resolve()
    browser: str = "chromium"  # chromium|firefox|webkit


def load_settings() -> ClaimBotSettings:
    _maybe_load_dotenv()
    base = _env("DASH_DN_CLAIM_BASE_URL", _env("OMS_BASE_URL", "")).rstrip("/") + "/"
    # Если дали только OMS_BASE_URL, достраиваем до /claim/ambulatory/
    if base.endswith("/"):
        pass
    if base.endswith("9000/") and "claim/ambulatory" not in base:
        base = base + "claim/ambulatory/"
    if not base.endswith("/"):
        base += "/"

    headless = _env("CLAIM_BOT_HEADLESS", "true").lower() == "true"
    try:
        slow = int(_env("CLAIM_BOT_SLOWMO_MS", "0"))
    except ValueError:
        slow = 0

    art = _env("CLAIM_BOT_ARTIFACTS_DIR", "")
    art_path = Path(art).resolve() if art else (Path(__file__).resolve().parents[3] / "artifacts").resolve()

    browser = _env("CLAIM_BOT_BROWSER", _env("OMS_BROWSER", "chromium")).lower()
    if browser in {"chrome", "googlechrome"}:
        browser = "chromium"
    if browser not in {"chromium", "firefox", "webkit"}:
        browser = "chromium"

    return ClaimBotSettings(
        base_url=base,
        username=_env("CLAIM_BOT_USERNAME", _env("OMS_USERNAME", "")),
        password=_env("CLAIM_BOT_PASSWORD", _env("OMS_PASSWORD", "")),
        headless=headless,
        slowmo_ms=max(0, slow),
        artifacts_dir=art_path,
        browser=browser,
    )


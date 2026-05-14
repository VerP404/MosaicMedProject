from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from apps.dash_dn.claim_bot.browser import open_context  # noqa: E402
from apps.dash_dn.claim_bot.settings import load_settings  # noqa: E402
from apps.dash_dn.claim_bot.worker import _login, _looks_like_login  # noqa: E402


def main() -> None:
    s = load_settings()
    with open_context(s, storage_state_path=None) as (_pw, _br, ctx):
        p = ctx.new_page()
        p.goto(s.base_url + "23020633", wait_until="domcontentloaded")
        if _looks_like_login(p):
            root = s.base_url.split("/claim/")[0].rstrip("/") + "/"
            _login(p, root, s.username, s.password)
            p.goto(s.base_url + "23020633", wait_until="domcontentloaded")
        p.wait_for_timeout(1500)
        loc = p.locator("[id*='combobox-service']")
        print("combobox-service count:", loc.count())
        for j in range(min(20, loc.count())):
            print(" -", loc.nth(j).get_attribute("id"))
        p.screenshot(path=str((s.artifacts_dir / "debug_ids.png").resolve()), full_page=True)


if __name__ == "__main__":
    main()


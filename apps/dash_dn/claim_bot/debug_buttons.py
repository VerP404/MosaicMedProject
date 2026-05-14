from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from apps.dash_dn.claim_bot.browser import open_context  # noqa: E402
from apps.dash_dn.claim_bot.claim_page import ClaimPage  # noqa: E402
from apps.dash_dn.claim_bot.settings import load_settings  # noqa: E402
from apps.dash_dn.claim_bot.worker import _login, _looks_like_login  # noqa: E402


def main() -> None:
    s = load_settings()
    with open_context(s, storage_state_path=None) as (_pw, _br, ctx):
        p = ctx.new_page()
        c = ClaimPage(p, base_url=s.base_url)
        c.open_talon("23020633")
        if _looks_like_login(p):
            root = s.base_url.split("/claim/")[0].rstrip("/") + "/"
            _login(p, root, s.username, s.password)
            c.open_talon("23020633")
        c.wait_ready()
        idx = c.list_service_indices()
        print("idx:", idx)
        for i in idx[:10]:
            inp = p.locator(f"#combobox-service-{i}").first
            btns = inp.locator("xpath=ancestor::div[contains(@class,'jss424')][1]//button").all()
            print("row", i, "buttons", len(btns))
            for b in btns:
                t = (b.get_attribute("title") or "").strip()
                if t:
                    print("  title:", t)


if __name__ == "__main__":
    main()


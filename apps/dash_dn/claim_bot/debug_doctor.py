from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# allow running as script
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from apps.dash_dn.claim_bot.browser import open_context  # noqa: E402
from apps.dash_dn.claim_bot.claim_page import ClaimPage  # noqa: E402
from apps.dash_dn.claim_bot.settings import load_settings  # noqa: E402
from apps.dash_dn.claim_bot.worker import _login, _looks_like_login  # noqa: E402


def main() -> None:
    os.environ.setdefault("CLAIM_BOT_HEADLESS", "true")
    os.environ.setdefault("CLAIM_BOT_BROWSER", "chromium")

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
        print("default doctor id:", c._default_doctor_id())

        i = c.ensure_empty_service_row()
        c.select_service_by_code(i, "A04.20.001")
        rows = c.read_services()
        print("rows:", [(r.index, r.code, r.doctor) for r in rows])
        i2 = [r.index for r in rows if str(r.code).startswith("A04.20.001")][0]

        doc_inp = p.locator(f"#doctor-service-{i2}").first
        print("doctor input count:", doc_inp.count())
        wrap = doc_inp.locator("xpath=ancestor::div[contains(@class,'Select-control')]").first
        valwrap = wrap.locator("[id^='react-select-'][id$='--value']").first
        rid = valwrap.get_attribute("id") or ""
        print("react value id:", rid)

        doc_inp.click(force=True)
        doc_inp.fill("")
        doc_inp.type("00136001", delay=30)
        time.sleep(1)

        # now use production helper
        c.set_doctor(i2, "00136001")
        rows2 = c.read_services()
        print("rows after set_doctor:", [(r.index, r.code, r.doctor) for r in rows2])

        lst = p.locator("[id$='--list']")
        print("list count:", lst.count())
        opt = p.locator("div.Select-menu-outer div.Select-option")
        print("opt count:", opt.count())
        if opt.count():
            print("first opt:", (opt.first.inner_text() or "")[:80])

        out = str((s.artifacts_dir / "debug_doctor.png").resolve())
        p.screenshot(path=out, full_page=True)
        print("screenshot:", out)


if __name__ == "__main__":
    main()


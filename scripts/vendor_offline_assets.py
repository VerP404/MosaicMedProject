#!/usr/bin/env python3
"""Скачивает CSS/JS/шрифты, чтобы Dash и Django работали без CDN."""
from __future__ import annotations

import shutil
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTX = ssl.create_default_context()

FILES = [
    # Bootstrap Icons (Dash: путь как в assets/css/bootstrap-icons.css)
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2",
        "apps/analytical_app/assets/fonts/bootstrap-icons/bootstrap-icons.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff",
        "apps/analytical_app/assets/fonts/bootstrap-icons/bootstrap-icons.woff",
    ),
    # Font Awesome 5 (пути из assets/css/all.min.css)
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-solid-900.woff2",
        "apps/analytical_app/assets/webfonts/fa-solid-900.woff2",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-solid-900.woff",
        "apps/analytical_app/assets/webfonts/fa-solid-900.woff",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-regular-400.woff2",
        "apps/analytical_app/assets/webfonts/fa-regular-400.woff2",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-regular-400.woff",
        "apps/analytical_app/assets/webfonts/fa-regular-400.woff",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-brands-400.woff2",
        "apps/analytical_app/assets/webfonts/fa-brands-400.woff2",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-brands-400.woff",
        "apps/analytical_app/assets/webfonts/fa-brands-400.woff",
    ),
    # Django: Font Awesome 6
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
        "static/vendor/fontawesome/css/all.min.css",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-solid-900.woff2",
        "static/vendor/fontawesome/webfonts/fa-solid-900.woff2",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-regular-400.woff2",
        "static/vendor/fontawesome/webfonts/fa-regular-400.woff2",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-brands-400.woff2",
        "static/vendor/fontawesome/webfonts/fa-brands-400.woff2",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-v4compatibility.woff2",
        "static/vendor/fontawesome/webfonts/fa-v4compatibility.woff2",
    ),
    # Django: Bootstrap Icons
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
        "static/vendor/bootstrap-icons/bootstrap-icons.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2",
        "static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff",
        "static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff",
    ),
    # Leaflet
    (
        "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
        "static/vendor/leaflet/leaflet.css",
    ),
    (
        "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
        "static/vendor/leaflet/leaflet.js",
    ),
    (
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        "static/vendor/leaflet/images/marker-icon.png",
    ),
    (
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        "static/vendor/leaflet/images/marker-icon-2x.png",
    ),
    (
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        "static/vendor/leaflet/images/marker-shadow.png",
    ),
    (
        "https://unpkg.com/leaflet@1.9.4/dist/images/layers.png",
        "static/vendor/leaflet/images/layers.png",
    ),
    (
        "https://unpkg.com/leaflet@1.9.4/dist/images/layers-2x.png",
        "static/vendor/leaflet/images/layers-2x.png",
    ),
    # Leaflet.Draw
    (
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css",
        "static/vendor/leaflet-draw/leaflet.draw.css",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js",
        "static/vendor/leaflet-draw/leaflet.draw.js",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/images/spritesheet.png",
        "static/vendor/leaflet-draw/images/spritesheet.png",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/images/spritesheet-2x.png",
        "static/vendor/leaflet-draw/images/spritesheet-2x.png",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/images/spritesheet.svg",
        "static/vendor/leaflet-draw/images/spritesheet.svg",
    ),
    # CodeMirror
    (
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.0/codemirror.min.css",
        "static/vendor/codemirror/codemirror.min.css",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.0/codemirror.min.js",
        "static/vendor/codemirror/codemirror.min.js",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.0/mode/sql/sql.min.js",
        "static/vendor/codemirror/sql.min.js",
    ),
    # Inter (latin + cyrillic)
    (
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/latin-300-normal.woff2",
        "static/vendor/inter/inter-latin-300.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/latin-400-normal.woff2",
        "static/vendor/inter/inter-latin-400.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/latin-600-normal.woff2",
        "static/vendor/inter/inter-latin-600.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/cyrillic-300-normal.woff2",
        "static/vendor/inter/inter-cyrillic-300.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/cyrillic-400-normal.woff2",
        "static/vendor/inter/inter-cyrillic-400.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/cyrillic-600-normal.woff2",
        "static/vendor/inter/inter-cyrillic-600.woff2",
    ),
]

INTER_CSS = """\
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 300;
  font-display: swap;
  src: url("inter-cyrillic-300.woff2") format("woff2");
  unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 300;
  font-display: swap;
  src: url("inter-latin-300.woff2") format("woff2");
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("inter-cyrillic-400.woff2") format("woff2");
  unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("inter-latin-400.woff2") format("woff2");
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("inter-cyrillic-600.woff2") format("woff2");
  unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("inter-latin-600.woff2") format("woff2");
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
"""


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "MosaicMedProject-offline-vendor"})
    with urllib.request.urlopen(req, context=CTX, timeout=60) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"[OK] {dest.relative_to(ROOT)} ({len(data)} bytes)")


def copy_shared_dash_assets() -> None:
    src_css = ROOT / "apps/analytical_app/assets/css/bootstrap.min.css"
    src_bi = ROOT / "apps/analytical_app/assets/css/bootstrap-icons.css"
    src_fonts = ROOT / "apps/analytical_app/assets/fonts/bootstrap-icons"

    dest_css = ROOT / "apps/chief_app/assets/css/bootstrap.min.css"
    dest_css.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_css, dest_css)
    dest_bi = ROOT / "apps/chief_app/assets/css/bootstrap-icons.css"
    shutil.copy2(src_bi, dest_bi)
    dest_fonts = ROOT / "apps/chief_app/assets/fonts/bootstrap-icons"
    dest_fonts.mkdir(parents=True, exist_ok=True)
    for item in src_fonts.iterdir():
        shutil.copy2(item, dest_fonts / item.name)
    print("[OK] chief_app assets: bootstrap + bootstrap-icons")

    masterd_css = ROOT / "apps/masterd_dashboard/assets/css/bootstrap.min.css"
    masterd_css.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_css, masterd_css)
    print("[OK] masterd_dashboard assets: bootstrap")


def main() -> int:
    failed = []
    for url, rel in FILES:
        dest = ROOT / rel
        try:
            download(url, dest)
        except Exception as exc:
            print(f"[ERR] {rel}: {exc}")
            failed.append(rel)
    inter_css = ROOT / "static/vendor/inter/inter.css"
    inter_css.parent.mkdir(parents=True, exist_ok=True)
    inter_css.write_text(INTER_CSS, encoding="utf-8")
    print(f"[OK] {inter_css.relative_to(ROOT)}")
    try:
        copy_shared_dash_assets()
    except Exception as exc:
        print(f"[ERR] dash assets copy: {exc}")
        failed.append("dash-copy")
    if failed:
        print("Failed:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

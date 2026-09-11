#!/usr/bin/env python3
"""렌더한 PNG 의 일부를 확대해 본다. 라벨 관통 검수용.

  python3 drawio_crop.py <png> <x> <y> <w> <h> [--zoom 2] [-o crop.png]

전체 1장을 축소해 보면 1.2px 선이 글자 획으로 보여 라벨 관통이 드러나지 않는다.
그룹 박스의 좌상단(라벨이 있는 곳)과 긴 캡션 주변을 최소 2배로 확대해 개별로 확인한다.
PIL·ImageMagick 없이 돌도록 렌더러와 같은 헤드리스 Chromium 을 쓴다.
"""
import argparse, os, subprocess, sys, tempfile, glob

def find_chrome():
    for p in ("chromium", "chromium-browser", "google-chrome"):
        r = subprocess.run(["which", p], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    for pat in ("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome",
                "~/.cache/puppeteer/chrome/*/chrome-linux*/chrome"):
        g = glob.glob(os.path.expanduser(pat))
        if g:
            return g[0]
    sys.exit("Chromium 없음")

ap = argparse.ArgumentParser()
ap.add_argument("png"); ap.add_argument("x", type=int); ap.add_argument("y", type=int)
ap.add_argument("w", type=int); ap.add_argument("h", type=int)
ap.add_argument("--zoom", type=float, default=2.0); ap.add_argument("-o", default="crop.png")
a = ap.parse_args()

src = os.path.abspath(a.png)
html = (f'<html><body style="margin:0;background:#fff">'
        f'<div style="width:{a.w}px;height:{a.h}px;overflow:hidden;position:relative">'
        f'<img src="file://{src}" style="position:absolute;left:{-a.x}px;top:{-a.y}px">'
        f'</div></body></html>')
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
    f.write(html); page = f.name
subprocess.run([find_chrome(), "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                "--virtual-time-budget=8000", f"--force-device-scale-factor={a.zoom}",
                f"--window-size={a.w},{a.h}", f"--screenshot={a.o}", f"file://{page}"],
               capture_output=True)
os.unlink(page)
print(a.o, os.path.getsize(a.o) // 1024, "KB")

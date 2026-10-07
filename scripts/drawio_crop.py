#!/usr/bin/env python3
"""렌더한 PNG 의 일부를 확대해 본다. 라벨 관통 검수용.

  python3 drawio_crop.py <png> <x> <y> <w> <h> [--zoom 2] [-o crop.png]

전체 1장을 축소해 보면 1.2px 선이 글자 획으로 보여 라벨 관통이 드러나지 않는다.
그룹 박스의 좌상단(라벨이 있는 곳)과 긴 캡션 주변을 최소 2배로 확대해 개별로 확인한다.
PIL·ImageMagick 없이 돌도록 렌더러와 같은 헤드리스 Chromium 을 쓴다.
"""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawio_render import find_chrome  # noqa: E402  Windows Chrome 경로까지 찾는 쪽을 공유한다

ap = argparse.ArgumentParser()
ap.add_argument("png"); ap.add_argument("x", type=int); ap.add_argument("y", type=int)
ap.add_argument("w", type=int); ap.add_argument("h", type=int)
ap.add_argument("--zoom", type=float, default=2.0); ap.add_argument("-o", default="crop.png")
a = ap.parse_args()
out = os.path.abspath(a.o)   # Chromium 은 상대 경로를 자기 작업 디렉토리 기준으로 푼다

src = os.path.abspath(a.png)
html = (f'<html><body style="margin:0;background:#fff">'
        f'<div style="width:{a.w}px;height:{a.h}px;overflow:hidden;position:relative">'
        f'<img src="{Path(src).as_uri()}" style="position:absolute;left:{-a.x}px;top:{-a.y}px">'
        f'</div></body></html>')
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html); page = f.name
subprocess.run([find_chrome(), "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                "--virtual-time-budget=8000", f"--force-device-scale-factor={a.zoom}",
                f"--window-size={a.w},{a.h}", f"--screenshot={out}", Path(page).as_uri()],
               capture_output=True)
os.unlink(page)
if not os.path.exists(out):
    sys.exit("크롭 실패")
print(out, os.path.getsize(out) // 1024, "KB")

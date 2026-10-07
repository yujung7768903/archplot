#!/usr/bin/env python3
"""`.drawio` 파일을 헤드리스 Chromium + draw.io viewer 로 PNG 로 렌더한다.

drawio Desktop CLI 가 없는 환경(sudo 불가, xvfb 없음)에서 쓰기 위한 것.
mxGeometry 좌표로 캔버스 크기를 미리 계산하므로 여백이 남지 않는다.

  python3 drawio_render.py in.drawio [-o out.png] [--scale 2]
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from html import escape as _esc

# Windows 콘솔 기본 인코딩(cp949)으로는 한글 출력이 깨지거나 UnicodeEncodeError 가 난다.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

PAD = 50          # 캔버스 사방 여백. 캡션이 노드 폭을 넘어가므로 필요하다.
HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER = os.path.join(HERE, "..", "vendor", "viewer-static.min.js")
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    os.path.expanduser("~/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"),
    os.path.expanduser("~/.cache/puppeteer/chrome/linux-152.0.7977.42/chrome-linux64/chrome"),
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    for p in ("chromium", "chromium-browser", "google-chrome"):
        hit = shutil.which(p)        # Windows 에는 which 명령이 없다
        if hit:
            return hit
    # playwright 버전이 바뀌면 위 경로가 어긋난다 — glob 로 재탐색
    import glob
    for pat in ("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome",
                "~/.cache/puppeteer/chrome/*/chrome-linux*/chrome"):
        got = glob.glob(os.path.expanduser(pat))
        if got:
            return got[0]
    sys.exit("Chromium 을 찾지 못했다. CHROME_CANDIDATES 를 확인하라.")


def canvas_size(xml):
    """mxGeometry 의 x+width / y+height 최대값으로 캔버스 크기를 구한다."""
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for m in re.finditer(r'<mxGeometry\b[^>]*>', xml):
        g = m.group(0)
        def num(k):
            v = re.search(rf'{k}="(-?[\d.]+)"', g)
            return float(v.group(1)) if v else None
        x, y, gw, gh = num("x"), num("y"), num("width"), num("height")
        if x is None or y is None:      # 엣지 라벨 등 상대 좌표는 건너뛴다
            continue
        x0, y0 = min(x0, x), min(y0, y)
        x1, y1 = max(x1, x + (gw or 0)), max(y1, y + (gh or 0))
    if x0 == float("inf"):
        return 1200, 800
    # viewer 가 내용을 원점으로 정규화하므로 max 가 아니라 (max - min) 이 실제 크기다.
    # 캡션이 노드 아래·좌우 바깥으로 나가므로 사방에 여유를 준다 (하단은 캡션 한 줄 더).
    return int(x1 - x0 + 2 * PAD), int(y1 - y0 + 2 * PAD + 30)


def render(src, out, scale=2.0):
    # Chromium 은 상대 경로를 자기 작업 디렉토리 기준으로 풀어 Windows 에서 쓰기가 거부된다.
    out = os.path.abspath(out)
    xml = open(src, encoding="utf-8").read()
    w, h = canvas_size(xml)
    cfg = {"nav": False, "resize": True, "toolbar": "", "xml": xml}
    html = (
        '<html><head><meta charset="utf-8">'
        '<style>html,body{margin:0;padding:0;background:#fff}</style></head><body>'
        f'<div class="mxgraph" data-mxgraph="{_esc(json.dumps(cfg), quote=True)}"></div>'
        f'<script src="{Path(VIEWER).resolve().as_uri()}"></script></body></html>'
    )
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        page = f.name
    cmd = [find_chrome(), "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--virtual-time-budget=10000", f"--force-device-scale-factor={scale}",
           f"--window-size={w},{h}", f"--screenshot={out}", Path(page).as_uri()]
    # Chromium 로그에 OS 언어 메시지가 섞인다. 로캘 인코딩(cp949)으로 읽으면 리더 스레드가 죽는다.
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.unlink(page)
    if not os.path.exists(out):
        sys.exit(f"렌더 실패\n{(r.stderr or '')[-800:]}")
    print(f"{out}  ({w}x{h} @{scale}x)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("--scale", type=float, default=2.0)
    a = ap.parse_args()
    render(a.src, a.out or re.sub(r"\.drawio(\.xml)?$", "", a.src) + ".png", a.scale)

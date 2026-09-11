#!/usr/bin/env python3
"""렌더한 PNG 를 Confluence 페이지에 붙인다 (없으면 페이지를 만든다).

  # 부모 밑에 새 페이지를 만들고 첨부
  confluence_publish.py out.png --parent 1234 --space KEY --title "제목"

  # 기존 페이지의 첨부만 갱신 (본문은 건드리지 않는다)
  confluence_publish.py out.png --page 5678

인증은 환경변수 CONFLUENCE_EMAIL / CONFLUENCE_API_TOKEN, 사이트는 CONFLUENCE_SITE.
confluence-skill 의 upload_confluence_v2.py 는 마크다운 문서를 페이지 본문으로
올리는 도구라 PNG 단독 첨부·갱신 경로가 없고 인증 변수도 다르다. 그래서 별도다.

첨부 갱신에 함정이 있다. 같은 파일명으로 POST /child/attachment 를 다시 부르면
새 버전이 생기지 않고 조용히 실패한다. 기존 첨부 id 를 찾아
POST /child/attachment/{id}/data 로 보내야 버전이 올라간다.
"""
import argparse
import base64
import hashlib
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

SITE = os.environ.get("CONFLUENCE_SITE", "").rstrip("/")
if not SITE:
    sys.exit("CONFLUENCE_SITE 가 필요하다 (예: https://<사이트>.atlassian.net).")
BASE = f"{SITE}/wiki/rest/api"


def _auth():
    email = os.environ.get("CONFLUENCE_EMAIL")
    token = os.environ.get("CONFLUENCE_API_TOKEN")
    if not (email and token):
        sys.exit("CONFLUENCE_EMAIL / CONFLUENCE_API_TOKEN 이 필요하다.")
    return "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()


def _req(method, url, data=None, headers=None):
    h = {"Authorization": _auth()}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url}\nHTTP {e.code}: {e.read()[:500].decode(errors='replace')}")


def _multipart(path):
    """첨부 업로드용 multipart 바디. requests 없이 표준 라이브러리만 쓴다."""
    boundary = uuid.uuid4().hex
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        content = f.read()
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n').encode() + content + \
        f"\r\n--{boundary}--\r\n".encode()
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}",
                  "X-Atlassian-Token": "no-check"}


def create_page(space, parent, title, filename):
    body = ('<p><ac:image ac:align="center" ac:layout="center">'
            f'<ri:attachment ri:filename="{filename}" /></ac:image></p>')
    payload = {"type": "page", "title": title, "space": {"key": space},
               "ancestors": [{"id": str(parent)}],
               "body": {"storage": {"value": body, "representation": "storage"}}}
    r = _req("POST", f"{BASE}/content", json.dumps(payload).encode(),
             {"Content-Type": "application/json"})
    return r["id"], r["_links"]["base"] + r["_links"]["webui"]


def _find(page_id, name):
    atts = _req("GET", f"{BASE}/content/{page_id}/child/attachment?limit=100")
    return next((a for a in atts.get("results", []) if a["title"] == name), None)


def attach(page_id, path):
    name = os.path.basename(path)
    hit = _find(page_id, name)
    body, headers = _multipart(path)
    url = (f"{BASE}/content/{page_id}/child/attachment/{hit['id']}/data" if hit
           else f"{BASE}/content/{page_id}/child/attachment")
    r = _req("POST", url, body, headers)
    got = r if "version" in r else (r.get("results") or [{}])[0]
    return got.get("version", {}).get("number"), got.get("extensions", {}).get("fileSize")


def verify(page_id, path):
    """올린 바이트가 페이지의 첨부와 같은지 확인한다."""
    hit = _find(page_id, os.path.basename(path))
    if not hit:
        return False
    req = urllib.request.Request(SITE + "/wiki" + hit["_links"]["download"],
                                 headers={"Authorization": _auth()})
    with urllib.request.urlopen(req) as r:
        remote = hashlib.md5(r.read()).hexdigest()
    return remote == hashlib.md5(open(path, "rb").read()).hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--page", help="기존 페이지 id. 주면 첨부만 갱신한다")
    ap.add_argument("--parent", help="새 페이지를 만들 부모 id")
    ap.add_argument("--space", help="스페이스 키 (새 페이지용)")
    ap.add_argument("--title", help="새 페이지 제목")
    a = ap.parse_args()

    if a.page:
        pid, url = a.page, f"{SITE}/wiki/spaces/_/pages/{a.page}"
    else:
        if not (a.parent and a.space and a.title):
            sys.exit("--page 또는 (--parent --space --title) 이 필요하다.")
        pid, url = create_page(a.space, a.parent, a.title, os.path.basename(a.image))
        print(f"페이지 생성: {url}")

    ver, size = attach(pid, a.image)
    print(f"첨부 v{ver} ({size} bytes)")
    print("md5 일치" if verify(pid, a.image) else "!! 업로드된 바이트가 로컬과 다르다")
    print(url)

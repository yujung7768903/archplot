#!/usr/bin/env python3
"""`.drawio` 아키텍처 다이어그램 빌더.

좌표를 직접 지정한다 — 자동 배치가 아니므로 라벨 겹침·빈 여백을 통제할 수 있다.
아이콘은 `diagrams` 패키지가 번들한 클라우드 공식 아이콘 PNG 를 data URI 로 심는다.
외부 파일 참조가 없어 `.drawio` 하나로 자립한다.

    from drawio_build import Diagram, icon

    d = Diagram()
    d.group("acct", "운영 계정", 200, 80, 400, 200)
    d.node("api", "API", 260, 140, icon("aws/compute/ec2"))
    d.node("db",  "DB",  480, 140, icon("aws/database/aurora"))
    d.edge("e1", "저장", "api", "db", exit=(1, 0.5), entry=(0, 0.5))
    d.save("out.drawio")

렌더는 `drawio_render.py out.drawio` 로 한다.
"""
import base64
import glob
import os
import xml.etree.ElementTree as ET
import xml.sax.saxutils as su


# 라벨은 전부 XML 속성값(value="...") 자리에 들어간다. saxutils.escape 는 & < > 만
# 바꾸고 따옴표는 그냥 두므로, 라벨에 " 가 하나 있으면 속성이 거기서 끝나 버린다.
# 그러면 파일은 정상적으로 써지고 생성기도 성공으로 끝나는데, viewer 가 그 지점부터
# 뒤쪽 셀을 통째로 버려 PNG 에서 노드가 조용히 사라진다. 두 따옴표를 다 바꾼다.
_ATTR_ESCAPE = {'"': "&quot;", "'": "&apos;"}


def _lbl(s):
    """라벨을 XML 속성값으로 안전하게 바꾼다.

    줄바꿈도 문자 참조로 바꾼다 — 속성값의 생 개행은 XML 파서가 공백으로 정규화해 버린다.
    """
    return su.escape(s, _ATTR_ESCAPE).replace("\n", "&#10;")



def _assert_wellformed(xml):
    """깨진 XML 을 파일로 내보내지 않는다.

    draw.io viewer 는 파싱이 깨진 지점부터 뒤쪽 셀을 조용히 버린다. 캔버스 크기는
    정규식으로 재서 정상으로 나오기 때문에, 렌더된 PNG 만 보면 노드가 사라진 걸
    알아채기 어렵다. 그래서 쓰기 전에 막는다.
    """
    try:
        ET.fromstring(xml)
    except ET.ParseError as e:
        col = e.position[1]
        near = xml[max(0, col - 120):col + 40]
        raise ValueError(
            f"생성한 XML 이 깨졌다 ({e}). 라벨에 XML 속성을 깨는 문자가 들어갔을 수 있다.\n"
            f"문제 지점 앞뒤: ...{near}...") from None

# `diagrams` 패키지의 아이콘 리소스. 경로가 파이썬 버전에 묶이므로 glob 로 찾는다.
_ICON_ROOTS = sorted(glob.glob(os.path.expanduser(
    "~/.local/lib/python3.*/site-packages/resources"))) or sorted(glob.glob(
    os.path.expanduser("~/.local/share/venvs/*/lib/python3.*/site-packages/resources")))

NODE = 78          # 아이콘 표준 크기
GRID = 20          # 좌표는 이 격자에 맞춘다

_IMG = ("shape=image;html=1;imageAspect=0;aspect=fixed;verticalLabelPosition=bottom;"
        "verticalAlign=top;labelPosition=center;align=center;fontColor=#232F3E;fontSize=12;"
        "image=data:image/png,{b64};")

# 경계 그룹. draw.io 의 AWS4 그룹 도형 정의를 그대로 쓴다.
_GROUP = ("outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;"
          "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;"
          "grIcon=mxgraph.aws4.{gr};strokeColor={stroke};fillColor=none;verticalAlign=top;"
          "align=left;spacingLeft=30;fontColor={stroke};dashed={dashed};")

# 경계 종류 → (grIcon, stroke, dashed). draw.io Sidebar-AWS4.js 정의에서 확인한 값.
BOUNDARY = {
    "account":     ("group_account", "#CD2264", 0),
    "cloud":       ("group_aws_cloud_alt", "#232F3E", 0),
    "region":      ("group_region", "#00A4A6", 1),
    "vpc":         ("group_vpc2", "#8C4FFF", 0),
    "subnet":      ("group_security_group", "#00A4A6", 0),
    "autoscaling": ("group_auto_scaling_group", "#D86613", 1),
    "onpremise":   ("group_corporate_data_center", "#7D8998", 0),
}

_EDGE = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=blockThin;endFill=1;"
         "strokeColor=#232F3E;strokeWidth=1.2;fontSize=11;fontColor=#232F3E;"
         "labelBackgroundColor=none;jumpStyle=none;")


def icon(relpath):
    """`diagrams` 리소스 상대경로로 아이콘 style 을 만든다 (`.png` 는 생략 가능).

    예: icon("aws/compute/ec2"), icon("aws/storage/simple-storage-service-s3"),
        icon("onprem/client/user"), icon("gcp/compute/gke")
    """
    if not relpath.endswith(".png"):
        relpath += ".png"
    for root in _ICON_ROOTS:
        path = os.path.join(root, relpath)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return _IMG.format(b64=base64.b64encode(f.read()).decode())
    raise FileNotFoundError(
        f"아이콘 없음: {relpath}\n찾은 리소스 루트: {_ICON_ROOTS or '(없음)'}\n"
        f"이름을 모르면 find_icon() 으로 검색하라.")


def find_icon(keyword, limit=20):
    """아이콘 이름을 모를 때 키워드로 찾는다. 반환값을 icon() 에 그대로 넣는다."""
    hits = []
    for root in _ICON_ROOTS:
        for p in glob.glob(os.path.join(root, "**", f"*{keyword}*.png"), recursive=True):
            hits.append(os.path.relpath(p, root)[:-4])
    return sorted(set(hits))[:limit]


class Diagram:
    def __init__(self, name="diagram"):
        self.name = name
        self._groups = []      # 그룹은 노드보다 먼저 출력해 아래에 깔린다
        self._cells = []

    def group(self, cid, label, x, y, w, h, kind="account"):
        gr, stroke, dashed = BOUNDARY[kind]
        st = _GROUP.format(gr=gr, stroke=stroke, dashed=dashed)
        self._groups.append(self._vertex(cid, label, st, x, y, w, h))
        return self

    def node(self, cid, label, x, y, style, w=NODE, h=NODE):
        self._cells.append(self._vertex(cid, label, style, x, y, w, h))
        return self

    def edge(self, cid, label, src, dst, exit=None, entry=None,
             dashed=False, waypoints=None, label_pos=None, label_offset=None):
        """exit/entry: (x, y) 를 0~1 비율로. 안 주면 draw.io 가 임의로 붙어 캡션을 덮는다.

        waypoints: [(x, y), ...] 우회 경로. label_pos: -1~1 선 위 라벨 위치.
        label_offset: (dx, dy) 픽셀 미세 조정.
        """
        st = _EDGE
        if exit:
            st += f"exitX={exit[0]};exitY={exit[1]};"
        if entry:
            st += f"entryX={entry[0]};entryY={entry[1]};"
        if dashed:
            st += "dashed=1;dashPattern=6 4;"
        xattr = f' x="{label_pos}"' if label_pos is not None else ""
        geo = f'<mxGeometry{xattr} relative="1" as="geometry">'
        if waypoints:
            geo += '<Array as="points">' + "".join(
                f'<mxPoint x="{px}" y="{py}"/>' for px, py in waypoints) + "</Array>"
        if label_offset:
            geo += f'<mxPoint x="{label_offset[0]}" y="{label_offset[1]}" as="offset"/>'
        geo += "</mxGeometry>"
        self._cells.append(
            f'<mxCell id="{cid}" value="{_lbl(label)}" style="{st}" edge="1" parent="1" '
            f'source="{src}" target="{dst}">{geo}</mxCell>')
        return self

    @staticmethod
    def _vertex(cid, label, style, x, y, w, h):
        return (f'<mxCell id="{cid}" value="{_lbl(label)}" style="{style}" vertex="1" '
                f'parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
                f'as="geometry"/></mxCell>')

    def xml(self):
        return ('<mxfile host="app.diagrams.net">'
                f'<diagram name="{_lbl(self.name)}">'
                '<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" page="0" '
                'math="0" shadow="0"><root>'
                '<mxCell id="0"/><mxCell id="1" parent="0"/>'
                + "".join(self._groups) + "".join(self._cells) +
                "</root></mxGraphModel></diagram></mxfile>")

    def save(self, path):
        xml = self.xml()
        _assert_wellformed(xml)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"{path}  ({len(self._groups)} 경계, {len(self._cells)} 셀)")
        return path


def _demo():
    """자체 점검. 아이콘 조회·XML 구조가 깨지면 여기서 걸린다."""
    d = Diagram("demo")
    d.group("g", "운영 계정", 200, 80, 400, 200)
    d.node("a", "API", 260, 140, icon("aws/compute/ec2"))
    d.node("b", "DB", 480, 140, icon("aws/database/aurora"))
    d.edge("e", "저장", "a", "b", exit=(1, 0.5), entry=(0, 0.5))
    x = d.xml()
    assert x.count("<mxCell") == 6, x.count("<mxCell")   # root 2 + 그룹 1 + 노드 2 + 엣지 1
    assert "data:image/png," in x
    assert "grIcon=mxgraph.aws4.group_account" in x
    assert "exitX=1;exitY=0.5;" in x
    assert find_icon("lambda"), "아이콘 검색이 비었다 — diagrams 리소스 경로 확인"

    # 라벨의 따옴표가 속성을 깨지 않는지. 깨지면 viewer 가 뒤쪽 셀을 조용히 버린다.
    q = Diagram('제목 "인용"')
    q.node("a", '따옴표 "여기" 포함', 40, 40, icon("aws/compute/ec2"))
    q.node("b", "뒤 노드", 240, 40, icon("aws/compute/ec2"))
    got = [c.get("value") for c in ET.fromstring(q.xml()).iter("mxCell") if c.get("value")]
    assert got == ['따옴표 "여기" 포함', "뒤 노드"], got

    # 깨진 XML 은 파일로 내보내지 않는다
    bad = Diagram("t")
    bad._cells.append('<mxCell id="x" value="x" style="a="b"" vertex="1" parent="1"/>')
    try:
        bad.xml() and _assert_wellformed(bad.xml())
    except ValueError:
        pass
    else:
        raise AssertionError("깨진 XML 을 통과시켰다")
    print("demo OK")


if __name__ == "__main__":
    _demo()

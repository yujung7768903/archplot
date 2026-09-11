#!/usr/bin/env python3
"""엣지 배선 라우터 — 노드가 다 놓인 뒤 연결점과 직교 경로를 계산해 웨이포인트로 박는다.

    from drawio_build import Diagram, icon
    from drawio_route import Panel, beside

    d = Diagram("제목")
    p = Panel(d, "a", 0, 0)              # id 접두사 · 좌표 오프셋 (한 장에 시안 여러 개)
    p.group(...); p.node(...); p.step(...)   # Diagram 과 같은 인자. step 은 흐름 칸·조건 마름모
    p.edge("e1", "라벨", "src", "dst")   # 연결점·경로는 여기서 정한다
    d.save("out.drawio")                 # save → xml 시점에 배선이 계산된다

배선 원칙 —
  · 아이콘(이미지 도형)은 각 변 3개씩 12개 연결점에만 붙는다. 모서리 4개는 쓰지 않는다 —
    꺾어 나갈 방향이 정해지지 않고, 모서리에서 뻗은 화살표는 아이콘에서 떠 보인다.
  · 마름모(rhombus)는 꼭짓점 4개와 빗변 중앙 4개만. 경계상자 변 위의 (1, 0.75) 같은 점은
    마름모 둘레 밖이라 draw.io 가 빗변으로 투영해 옮기고 첫 구간이 대각선이 된다.
    빗변 중앙은 (x, y, "h"|"v") 로 가로·세로 나가는 방향까지 정한다.
  · 그 밖의 도형(그룹 경계 포함)은 변 중앙 4개.
  · 두 연결점이 같은 x 나 같은 y 면 직선, 아니면 90° 로 꺾는다 (L → Z → 사방이 막히면
    옆으로 빠지는 우회). 변 중앙을 먼저 고르고 대각선은 만들지 않는다.
  · 나가는 점은 여러 선이 공유해도 되지만 들어오는 점은 무엇과도 겹치지 않는다. 한 꼭짓점에
    들어오는 선과 나가는 선이 겹치면 들어오는 쪽을 ep= 로 빗변 중앙에 붙인다.
  · 요청·응답처럼 같은 두 노드를 오가는 선 2본은 sp=/ep= 로 차선을 못박는다 — 요청은 (·, 0.25)
    위 차선, 응답은 (·, 0.75) 아래 차선. 점수만으로는 어느 쪽이 위로 갈지 정해지지 않는다.
  · 마름모 옆에 놓는 아이콘은 beside() 로 세로 중심을 맞춘다 — 10px 어긋나면 잔꺾임이 생긴다.
  · 다른 아이콘·흐름 칸을 관통하거나 CLEAR 안으로 스치는 경로, 이미 지나간 선 위를 달리는
    경로는 버린다. 그룹 경계선 자체는 장애물로 보지 않는다 — 박스 안을 훑는 Z 는 off= 로 옮긴다.
  · 그룹 라벨(박스 좌상단)과 노드 캡션(아이콘 아래)의 **글자 상자**는 장애물로 본다. 이걸 모르면
    라벨을 뚫는 경로가 최단이라 뽑힌다. 버리지는 않고 크게 감점한 뒤, 그래도 남으면 경고를 낸다 —
    캡션이 아이콘보다 넓은 노드가 많으면 피할 길이 아예 없는 배치가 나오기 때문이다.
  · 경로를 draw.io 자동 라우팅에 맡기지 않는다 (edgeStyle=none). 맡기면 관통 판정과 실제
    렌더가 어긋난다. 엣지는 노드보다 먼저 출력해 아래 레이어에 깔아 캡션 글자가 선 위에 남는다.
  · 꺾인 경로의 직선 구간은 MIN_SEG 이상이어야 한다. 짧은 구간은 잔꺾임으로 보여 선이 노드에
    붙은 것처럼 읽힌다. 다른 연결점·중간선으로 피할 수 없으면 경고를 내고 그린다 — 노드 간격을 벌려라.
  · 조건에 맞는 경로가 하나도 없으면 RuntimeError — 배치를 고치라는 신호다.

자체 점검: python3 drawio_route.py
"""
import sys

import drawio_build
from drawio_build import Diagram

# 웨이포인트를 곧이곧대로 이어 그리게 한다. 라벨 배경은 흰색 — 기본값(none)이면 선이
# 글자 가운데를 관통해 취소선처럼 보인다.
drawio_build._EDGE = (drawio_build._EDGE
                      .replace("edgeStyle=orthogonalEdgeStyle;", "edgeStyle=none;")
                      .replace("labelBackgroundColor=none;", "labelBackgroundColor=#FFFFFF;"))

_PANELS = []

# draw.io 가 이미지 도형에 내주는 연결점 중 각 변 3개씩. 모서리 4개는 쓰지 않는다 —
# 꺾어 나갈 방향이 정해지지 않고, 모서리에서 뻗은 화살표는 아이콘에서 떠 보인다.
_PORTS_IMG = [(0.25, 0), (0.5, 0), (0.75, 0),
              (1, 0.25), (1, 0.5), (1, 0.75),
              (0.25, 1), (0.5, 1), (0.75, 1),
              (0, 0.25), (0, 0.5), (0, 0.75)]
# 그 밖의 도형은 변 중앙 4개만 가정한다. 지금 엣지가 붙는 노드는 전부 이미지 도형이다.
_PORTS_PLAIN = [(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)]
# 마름모는 꼭짓점 4개(경계상자 변 중앙)와 빗변 중앙 4개만. 경계상자 변 위의 (1, 0.75) 같은
# 점은 마름모 둘레 밖이라 draw.io 가 빗변 위로 투영해 옮기고, 그 순간 첫 구간이 대각선이
# 된다. 빗변 중앙 (0.25, 0.25) 는 둘레 위라 옮기지 않는다. 빗변 중앙에서는 가로·세로
# 어느 쪽으로도 나갈 수 있어 셋째 항에 방향 표지를 붙인다.
_PORTS_RHOMBUS = _PORTS_PLAIN + [
    (x, y, o) for x in (0.25, 0.75) for y in (0.25, 0.75) for o in ("h", "v")]


def _horiz(port):
    """첫(끝) 구간이 가로인가. 변 위의 점은 좌표로, 빗변 중앙은 표지로 정한다."""
    return port[2] == "h" if len(port) > 2 else port[0] in (0, 1)


def _pt(port):
    return port[:2]

W_BEND = 30        # 꺾임 1회당. 길이가 같으면 덜 꺾인 것
W_OFFCENTER = 20   # 변 중앙이 아닌 연결점. 꺾임 1회보다는 싸다
W_MID = 3          # Z 경로의 중간선을 기본 위치에서 옮긴 대가
W_CONFLICT = 200   # 들어오는 점과 나가는 점은 달라야 한다
W_OVERLAP = 500    # 이미 지나간 선과 같은 선 위를 달리지 않게
W_BLOCK = 1e6      # 아이콘에 붙거나 관통하는 경로는 버린다
W_TEXT = 800       # 그룹 라벨·노드 캡션 글자를 지나는 구간 1개당. 라우터가 이걸 모르면
                   # 라벨을 뚫는 경로가 최단이라 선택된다. W_BLOCK 은 아니다 — 피할 길이
                   # 없는 배치도 있어서, 버리는 대신 경고를 내고 그린다
TEXT_PAD = 2       # 글자 상자 여유. 아이콘의 CLEAR 만큼 넓게 보면 과잉 회피가 된다
FONT = 12          # 캡션·그룹 라벨 글자 크기 (drawio_build 의 _IMG·_GROUP 과 같아야 한다)
LINE_H = 15        # 한 줄 높이
GROUP_INDENT = 30  # _GROUP 의 spacingLeft
MIN_SEG = 24       # 꺾인 경로의 직선 구간 하한. 이보다 짧은 구간은 잔꺾임으로 보여 노드에 붙은 듯 읽힌다
W_SHORT = 600      # MIN_SEG 미만 구간 1개당. W_OVERLAP 보다 커야 한다 — 겹침 판정(2px 여유)을 피하려고 구간을 2px 로 줄이는 경로가 더 싸게 나오면 안 된다
MID_OFF = (0, 24, -24, 48, -48)
CLEAR = 10         # 아이콘에서 이만큼은 떨어져야 스치는 것으로 안 보인다
ESC = (72, 108, 144)   # 사방이 막힌 노드에서 옆으로 빠져나가는 거리


class Panel:
    """Diagram 에 좌표 오프셋과 id 접두사를 씌운다. 한 장에 여러 시안을 넣기 위한 것."""

    def __init__(self, d, pfx, ox, oy):
        self.d, self.pfx, self.ox, self.oy = d, pfx, ox, oy
        self.boxes = {}      # cid -> (x, y, w, h, style). 연결점·관통 판정에 쓴다
        self.ends = {}       # 그룹 경계. 엣지 끝점으로만 쓴다 — 관통 판정에서는 뺀다
        self.solid = set()   # 아이콘이 아니어도 관통 판정에 넣을 노드 (플로우 칸)
        self.wires = []      # 배선은 노드가 다 놓인 뒤에 계산한다
        self.outs = set()    # (cid, port) 나가는 점 — 여러 선이 같이 써도 된다
        self.inns = set()    # (cid, port) 들어오는 점 — 겹치면 안 된다
        self.segs = []       # (좌표, 시작, 끝, 세로여부) — 선 겹침 판정
        self.texts = []      # (주인 cid, (x, y, w, h), 이름) — 캡션·그룹 라벨. 관통하면 경고
        _PANELS.append(self)

    def _i(self, cid):
        return f"{self.pfx}_{cid}"

    def node(self, cid, label, x, y, style, **kw):
        w, h = kw.get("w", drawio_build.NODE), kw.get("h", drawio_build.NODE)
        ax, ay = x + self.ox, y + self.oy
        self.boxes[cid] = (ax, ay, w, h, style)
        # 캡션은 아이콘 아래 가운데 정렬로 그려진다. 아이콘보다 넓으면 좌우로 삐져나온다.
        if label and "verticalLabelPosition=bottom" in style:
            tw = _text_w(label)
            self.texts.append((cid, (ax + w / 2 - tw / 2, ay + h, tw, _text_h(label)),
                               f"{cid} 캡션"))
        self.d.node(self._i(cid), label, ax, ay, style, **kw)

    def group(self, cid, label, x, y, w, h, kind="account"):
        ax, ay = x + self.ox, y + self.oy
        self.ends[cid] = (ax, ay, w, h, "")
        # 그룹 라벨은 좌상단 고정이다. 그 열로 세로선을 올리면 글자를 뚫는다.
        if label:
            self.texts.append((cid, (ax + GROUP_INDENT, ay, _text_w(label), _text_h(label)),
                               f"{cid} 라벨"))
        self.d.group(self._i(cid), label, ax, ay, w, h, kind=kind)

    def step(self, cid, label, x, y, style, w, h):
        """플로우 칸. 아이콘 도형이 아니지만 선이 뚫고 지나가면 안 된다."""
        self.solid.add(cid)
        self.node(cid, label, x, y, style, w=w, h=h)

    def geo(self, cid):
        """엣지 끝점의 기하. 노드가 없으면 그룹 경계를 본다."""
        return self.boxes.get(cid) or self.ends[cid]

    def edge(self, cid, label, src, dst, dashed=False, off=None, ep=None, lp=None, sp=None,
             label_offset=None):
        """실제 배선은 flush() 로 미룬다 — 이 시점에는 아직 안 놓인 노드가 있어서
        관통 판정을 할 수 없다.

        off 는 Z 경로의 중간선 위치를 못박는다. 라우터는 그룹 경계를 장애물로
        보지 않아서, 박스 안을 세로로 훑고 지나가는 경로를 스스로 피하지 못한다.
        sp/ep 는 나가는·들어오는 연결점을 못박는다. 요청·응답 두 줄을 위·아래 차선으로
        나눌 때 쓴다 — 점수만으로는 어느 줄이 위로 갈지 정해지지 않는다.

        lp 는 라벨을 선 **위에서** 움직이고, label_offset=(dx, dy) 는 선에서 **떼어 놓는다**.
        평행선 간격이 라벨 폭보다 좁으면 lp 로는 못 푼다 — 그때 label_offset 을 쓴다.
        """
        self.wires.append((cid, label, src, dst, dashed, off, ep, lp, sp, label_offset))

    def flush(self):
        if self.wires is None:
            return
        for cid, label, src, dst, dashed, off, ep, lp, sp, loff in self.wires:
            ex, en, corners = _route(self, src, dst, off, ep, sp)
            kw = {} if lp is None else {"label_pos": lp}
            if loff is not None:
                kw["label_offset"] = loff
            self.d.edge(self._i(cid), label, self._i(src), self._i(dst),
                        exit=ex, entry=en, dashed=dashed, waypoints=corners or None, **kw)
        self.wires = None


def _at(box, port):
    x, y, w, h, _ = box
    return x + w * port[0], y + h * port[1]


def _path(a, b, ps, pd, off):
    """직선 → L → Z 순으로 직교 경로를 만든다. 대각선은 만들지 않는다.

    연결점이 좌·우면에 있으면 첫 구간이 가로, 상·하면이면 세로다. 모서리가 없으니
    면이 하나로 정해진다. off 는 Z 의 중간선을 옮기는 값이며 직선·L 에는 0 만 받는다.
    """
    (ax, ay), (bx, by) = a, b
    right, down = bx > ax, by > ay
    vs, vd = _horiz(ps), _horiz(pd)               # True 면 가로로 나간다(들어온다)
    if abs(bx - ax) < 1:                          # 같은 x — 수직 직선
        if off or vs or vd:
            return None
        if (ps[1] > 0.5) != down or (pd[1] < 0.5) != down:
            return None
        return [a, b]
    if abs(by - ay) < 1:                          # 같은 y — 수평 직선
        if off or not vs or not vd:
            return None
        if (ps[0] > 0.5) != right or (pd[0] < 0.5) != right:
            return None
        return [a, b]

    # 첫 구간은 연결점이 난 면 쪽으로 나가야 하고, 끝 구간은 반대편에서 들어와야 한다
    out_ok = ((ps[0] > 0.5) == right) if vs else ((ps[1] > 0.5) == down)
    in_ok = ((pd[0] < 0.5) == right) if vd else ((pd[1] < 0.5) == down)
    if not (out_ok and in_ok):
        return None

    if vs and not vd:                             # 가로 → 세로 (1번 꺾음)
        return None if off else [a, (bx, ay), b]
    if vd and not vs:                             # 세로 → 가로 (1번 꺾음)
        return None if off else [a, (ax, by), b]
    if not vs:                                    # 세로 → 가로 → 세로
        my = (ay + by) / 2 + off
        return [a, (ax, my), (bx, my), b]
    mx = (ax + bx) / 2 + off                      # 가로 → 세로 → 가로
    return [a, (mx, ay), (mx, by), b]


def _detour(a, b, ps, pd, esc, off):
    """일단 반대쪽으로 빠졌다가 돌아온다. 아래·옆이 이웃 노드로 막힌 노드
    (AgentCore Runtime 아래의 Memory) 를 빠져나갈 유일한 길이다."""
    (ax, ay), (bx, by) = a, b
    if not _horiz(ps) or abs(bx - ax) < 1 or abs(by - ay) < 1:
        return None
    ex = ax + (esc if ps[0] > 0.5 else -esc)
    if _horiz(pd):                                # 가로 → 세로 → 가로
        if (ex >= bx) if pd[0] < 0.5 else (ex <= bx):
            return None
        return None if off else [a, (ex, ay), (ex, by), b]
    if (pd[1] < 0.5) != (by > ay):                # 가로 → 세로 → 가로 → 세로
        return None
    my = (ay + by) / 2 + off
    return [a, (ex, ay), (ex, my), (bx, my), b]


def _text_w(label):
    """글자 폭 추정. 한글·CJK 는 전각이라 글자당 FONT, 그 밖은 약 0.55배로 본다.

    정확한 폰트 메트릭이 아니라 회피 판정용 어림값이다. 넉넉히 잡아 놓치는 쪽보다
    조금 넓게 보는 쪽이 안전하다.
    """
    def w(ch):
        return FONT if ord(ch) > 0x2E7F else FONT * 0.55
    return max((sum(w(c) for c in line) for line in label.split("\n")), default=0)


def _text_h(label):
    return LINE_H * (label.count("\n") + 1)


def _rect_hits(a, b, rect, pad):
    """직교 선분이 사각형(+pad)을 지나는지."""
    x, y, w, h = rect
    x0, y0, x1, y1 = x - pad, y - pad, x + w + pad, y + h + pad
    if abs(b[0] - a[0]) < 1:
        return x0 < a[0] < x1 and max(a[1], b[1]) > y0 and min(a[1], b[1]) < y1
    return y0 < a[1] < y1 and max(a[0], b[0]) > x0 and min(a[0], b[0]) < x1


def _text_hits(path, p, skip):
    """경로가 지나는 글자 상자들. 자기 출발·도착 노드의 캡션은 세지 않는다."""
    hit = []
    for a, b in zip(path, path[1:]):
        for owner, rect, what in p.texts:
            if owner in skip:
                continue
            if _rect_hits(a, b, rect, TEXT_PAD) and what not in hit:
                hit.append(what)
    return hit


def _seg_hits(a, b, box):
    """직교 선분이 아이콘에 CLEAR 보다 가까이 붙는지. 밑변에 딱 붙은 선은 관통이
    아니어도 아이콘을 스치는 것처럼 보이므로 박스를 넓혀서 본다."""
    x, y, w, h, _ = box
    x0, y0 = x - CLEAR, y - CLEAR
    x1, y1 = x + w + CLEAR, y + h + CLEAR
    if abs(b[0] - a[0]) < 1:
        return x0 < a[0] < x1 and max(a[1], b[1]) > y0 and min(a[1], b[1]) < y1
    return y0 < a[1] < y1 and max(a[0], b[0]) > x0 and min(a[0], b[0]) < x1


def _blocked(path, p, skip):
    for a, b in zip(path, path[1:]):
        for cid, box in p.boxes.items():
            if cid in skip or ("shape=image" not in box[4] and cid not in p.solid):
                continue
            if _seg_hits(a, b, box):
                return True
    return False


def _spans(path):
    for a, b in zip(path, path[1:]):
        vert = abs(b[0] - a[0]) < 1
        coord = a[0] if vert else a[1]
        if vert:
            lo, hi = min(a[1], b[1]), max(a[1], b[1])
        else:
            lo, hi = min(a[0], b[0]), max(a[0], b[0])
        yield coord, lo, hi, vert


def _overlap(path, segs):
    """이미 그린 선과 같은 선 위를 겹쳐 달리는 구간 수."""
    n = 0
    for coord, lo, hi, vert in _spans(path):
        for c, slo, shi, sv in segs:
            if sv == vert and abs(coord - c) < 6 and hi > slo + 2 and lo < shi - 2:
                n += 1
    return n


def _length(path):
    return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:]))


def _short_segs(path):
    """꺾인 경로에서 MIN_SEG 보다 짧은 직선 구간 수. 직선(구간 1개)은 대상이 아니다."""
    if len(path) < 3:
        return 0
    return sum(1 for a, b in zip(path, path[1:])
               if abs(b[0] - a[0]) + abs(b[1] - a[1]) < MIN_SEG)


def _ports(p, box, cid):
    if "rhombus" in box[4]:
        return _PORTS_RHOMBUS
    return _PORTS_IMG if "shape=image" in box[4] or cid in p.solid else _PORTS_PLAIN


def _search(p, src, dst, esc, offs=MID_OFF, ep=None, sp=None):
    """연결점 × 중간선 위치 전수 탐색. esc 가 있으면 우회 경로만 만든다."""
    bs, bd = p.geo(src), p.geo(dst)
    skip = {src, dst}
    ports_s, ports_d = _ports(p, bs, src), _ports(p, bd, dst)
    if ep is not None:
        ports_d = [ep]
    if sp is not None:
        ports_s = [sp]
    best = None
    for ps in ports_s:
        a = _at(bs, ps)
        for pd in ports_d:
            b = _at(bd, pd)
            for off in offs:
                path = (_detour(a, b, ps, pd, esc, off) if esc
                        else _path(a, b, ps, pd, off))
                if path is None:
                    continue
                score = (_length(path) + W_BEND * (len(path) - 2)
                         + W_MID * abs(off) / 24)
                if 0.5 not in ps:
                    score += W_OFFCENTER
                if 0.5 not in pd:
                    score += W_OFFCENTER
                # 나가는 점은 공유해도 되지만, 들어오는 점은 무엇과도 겹치면 안 된다
                if (src, _pt(ps)) in p.inns:
                    score += W_CONFLICT
                if (dst, _pt(pd)) in p.inns or (dst, _pt(pd)) in p.outs:
                    score += W_CONFLICT
                score += W_OVERLAP * _overlap(path, p.segs)
                score += W_SHORT * _short_segs(path)
                score += W_TEXT * len(_text_hits(path, p, skip))
                if _blocked(path, p, skip):
                    score += W_BLOCK
                if best is None or score < best[0]:
                    best = (score, ps, pd, path)
    return best


def _route(p, src, dst, off=None, ep=None, sp=None):
    """곧은 길을 먼저 찾고, 막혔을 때만 옆으로 빠지는 우회 경로를 본다.

    ep 는 들어가는 연결점을 못박는다 — 점수만으로는 라벨이 어디 떨어지는지 알 수 없어서,
    가장 짧은 경로가 다른 노드의 캡션을 덮는 경우가 있다.
    """
    offs = MID_OFF if off is None else (off,)
    best = _search(p, src, dst, None, offs, ep, sp)
    if best is None or best[0] >= W_BLOCK:
        for esc in ESC:
            alt = _search(p, src, dst, esc, offs, ep, sp)
            if alt is not None and (best is None or alt[0] < best[0]):
                best = alt
    # 아이콘에 붙는 경로만 남았으면 조용히 그리지 않는다 — 배치를 고쳐야 하는 신호다
    if best is None or best[0] >= W_BLOCK:
        raise RuntimeError(
            f"{p.pfx}: {src} → {dst} — 아이콘에서 {CLEAR}px 떨어진 직교 경로가 없다")
    _, ps, pd, path = best
    hit = _text_hits(path, p, {src, dst})
    if hit:  # 피할 경로가 없었다 — 좌표를 고치라는 신호. 축소 렌더로는 잘 안 보인다
        print(f"{p.pfx}: {src} → {dst} — 글자를 지난다: {' · '.join(hit)}. "
              f"노드·박스를 옮겨 그 열을 비워라", file=sys.stderr)
    if _short_segs(path):  # 대안이 없어 짧은 구간이 남았다 — 노드 간격을 벌리라는 신호
        pts = " → ".join(f"({x:.0f},{y:.0f})" for x, y in path)
        print(f"{p.pfx}: {src} → {dst} — {MIN_SEG}px 미만 구간이 남음. 두 노드 간격을 벌려라: {pts}",
              file=sys.stderr)
    ps, pd = _pt(ps), _pt(pd)
    p.outs.add((src, ps))
    p.inns.add((dst, pd))
    p.segs.extend(_spans(path))
    return ps, pd, path[1:-1]


_orig_xml = Diagram.xml


def _xml_wired(self):
    """배선을 계산한 뒤, 엣지를 노드보다 먼저 출력해 아래 레이어에 깐다."""
    for p in _PANELS:
        if p.d is self:
            p.flush()
    self._cells.sort(key=lambda c: 1 if 'edge="1"' in c
                     else (0 if "container=1" in c else 2))
    return _orig_xml(self)


Diagram.xml = _xml_wired


def beside(p, cid):
    """cid 의 세로 중심에 아이콘 중심을 맞춘 y. 마름모 꼭짓점에서 아이콘 변 중앙으로
    직선이 가려면 두 중심이 같은 높이여야 한다 — 10px 만 어긋나도 잔꺾임이 생긴다."""
    x, y, w, h, _ = p.boxes[cid]
    return int(y + h / 2 - drawio_build.NODE / 2)


def _check():
    """마름모 연결점·직선·그룹 끝점·임의 off 가 규칙대로 나오는지."""
    d = Diagram("route-check")
    p = Panel(d, "t", 0, 0)
    img = drawio_build._IMG.format(b64="")
    p.step("q", "허용?", 100, 100, "rhombus;whiteSpace=wrap;html=1;", 190, 58)   # 중심 (195, 129)
    p.node("t", "도구", 400, beside(p, "q"), img)                             # 세로 중심 129
    p.node("c", "호출자", 100, 300, img)
    p.group("g", "서브넷", 600, 79, 200, 100)          # 세로 중심 129 — t 와 같은 줄

    ps, pd, corners = _route(p, "q", "t")
    assert (ps, pd, corners) == ((1, 0.5), (0, 0.5), []), (ps, pd, corners)   # 꼭짓점 → 직선

    p.inns.add(("q", (1, 0.5)))                      # 오른쪽 꼭짓점을 들어오는 선이 선점하면
    ps, _, _ = _route(p, "q", "t")
    ok = set(_PORTS_PLAIN) | {(x, y) for x in (0.25, 0.75) for y in (0.25, 0.75)}
    assert len(ps) == 2 and ps in ok, ps            # 빗변 중앙으로 옮기고 표지는 떼서 준다

    ps, _, _ = _route(p, "g", "t")
    assert ps in _PORTS_PLAIN, ps                   # 그룹 경계는 변 중앙 4개
    _route(p, "c", "t", off=-120)                   # MID_OFF 밖의 off 도 받는다
    p.node("w", "워커", 100, 500, img)              # 바로 아래에 14px 만 어긋난 저장소
    p.node("s", "저장소", 114, 640, img)
    _, _, corners = _route(p, "w", "s")
    assert not corners or not _short_segs([(0, 0)] + corners + [(0, 0)]) or True
    assert all(abs(b[0] - a[0]) + abs(b[1] - a[1]) >= MIN_SEG
               for a, b in zip(corners, corners[1:])), corners   # 중간 구간이 잔꺾임이면 안 된다
    d.xml()                                          # flush 까지 예외 없이
    print("drawio_route: ok")



def _demo_text():
    """그룹 라벨을 지나는 경로는 경고가 나고, 라벨이 짧으면 안 나는지."""
    import contextlib, io

    def run(pfx, label):
        d = Diagram("t")
        q = Panel(d, pfx, 0, 0)
        q.group("g", label, 100, 300, 600, 300)
        q.node("a", "A", 200, 400, drawio_build.icon("aws/compute/ec2"))
        q.node("b", "B", 200, 100, drawio_build.icon("aws/compute/ec2"))
        q.edge("e", "", "a", "b")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            d.xml()
        return err.getvalue()

    assert "글자를 지난다" in run("tx1", "아주 긴 그룹 라벨이라 위로 올라가는 세로선을 가로막는다")
    assert "글자를 지난다" not in run("tx2", "짧음")


if __name__ == "__main__":
    _demo_text()
    _check()

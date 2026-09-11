#!/usr/bin/env python3
"""배선 라우터 예시. 연결점·직교 경로를 라우터가 정한다 — exit/entry/waypoints 를 손으로 안 준다.

  python3 examples/routed.py
  python3 scripts/drawio_render.py examples/routed.drawio

보여주는 것 — 조건 마름모, 마름모 옆 아이콘 세로 정렬(beside), 요청·응답 두 줄의 차선 고정(sp/ep).

두 가지를 피해서 배치했다.
  · 마름모와 아이콘은 연결점 격자가 다르다(마름모는 꼭짓점·빗변 중앙, 아이콘은 각 변 3개).
    억지로 붙이면 4px 잔꺾임이 남아 MIN_SEG 경고가 난다. 마름모에는 꼭짓점으로 직선만 붙인다.
  · 캡션은 아이콘 아래에 있다. 하단 면으로 선을 내면 캡션을 관통한다.
    요청·응답 두 줄은 좌·우 면에 y 차선(0.25 / 0.75)으로 나눈다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from drawio_build import Diagram, icon  # noqa: E402
from drawio_route import Panel, beside  # noqa: E402

DIAMOND = ("rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
           "strokeColor=#D86613;fontSize=11;")

d = Diagram("게이트웨이 인가 흐름")
p = Panel(d, "r", 0, 0)                       # id 접두사 · 좌표 오프셋

p.group("g_gw", "게이트웨이 계정", 180, 60, 940, 240)
p.group("g_data", "데이터 계정", 496, 380, 240, 200)

# 마름모는 선이 관통하지 못하는 도형이라 판정 지점에 쓴다.
p.step("allow", "권한 있나?", 520, 150, DIAMOND, 190, 58)

# 마름모 옆 아이콘은 beside() 로 세로 중심을 맞춘다. 10px 어긋나면 잔꺾임이 생긴다.
p.node("client", "담당자", 40, beside(p, "allow"), icon("onprem/client/user"))
p.node("gw", "게이트웨이", 260, beside(p, "allow"), icon("aws/network/api-gateway"))
p.node("judge", "인가 판정", 800, beside(p, "allow"), icon("aws/compute/lambda"))

# 마름모 아래 꼭짓점(x 615)과 세로 중심을 맞춘다 — 두 점이 한 줄로 떨어진다.
p.node("db", "조회 대상 DB", 576, 450, icon("aws/database/aurora"))
# 요청·응답 쌍은 캡션을 피해 옆에 둔다. 같은 크기 아이콘이라 y 차선이 정확히 맞는다.
p.node("perm", "권한 목록", 1000, beside(p, "allow"), icon("aws/database/dynamodb"))

p.edge("e1", "", "client", "gw")
p.edge("e2", "요청", "gw", "allow")
p.edge("e3", "판정 위임", "allow", "judge")
p.edge("e4", "허용분만 조회", "allow", "db")
# 같은 두 노드를 오가는 두 줄은 sp/ep 로 차선을 못박는다.
# 점수만으로는 어느 줄이 위로 갈지 정해지지 않아 두 줄이 겹친다.
p.edge("e5", "권한 조회", "judge", "perm", sp=(1, 0.25), ep=(0, 0.25))
p.edge("e6", "판정 결과", "perm", "judge", dashed=True, sp=(0, 0.75), ep=(1, 0.75))

d.save(os.path.join(HERE, "routed.drawio"))

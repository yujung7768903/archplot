#!/usr/bin/env python3
"""README 플로우차트 예시 — Teams Q&A 봇의 메시지 처리 흐름. 연결은 라우터가 정한다.

  python3 docs/flow.py
  python3 scripts/drawio_render.py docs/flow.drawio

주 흐름은 가로 한 줄, 분기는 마름모 아래 꼭짓점으로 내려 그 밑에 둔다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from drawio_build import Diagram  # noqa: E402
from drawio_route import Panel  # noqa: E402

START = "rounded=1;arcSize=50;whiteSpace=wrap;fillColor=#D5E8D4;strokeColor=#82B366;fontSize=12;"
PROC = "rounded=1;arcSize=8;whiteSpace=wrap;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;"
DEC = "rhombus;whiteSpace=wrap;fillColor=#FFE6CC;strokeColor=#D79B00;fontSize=12;"
END = "rounded=1;arcSize=50;whiteSpace=wrap;fillColor=#F8CECC;strokeColor=#B85450;fontSize=12;"
TITLE = ("text;html=0;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
         "fontSize=18;fontStyle=1;fontColor=#232F3E;")

CY, CY2 = 150, 320          # 주 흐름 · 분기 줄의 세로 중심
PH, DH = 60, 100            # 칸 · 마름모 높이

d = Diagram("메시지 처리 흐름")
p = Panel(d, "f", 0, 0)
p.node("title", "Teams Q&A 봇 — 메시지 처리 흐름", 40, 0, TITLE, w=600, h=40)


def box(cid, label, x, w, style=PROC, cy=CY):
    p.step(cid, label, x, cy - PH // 2, style, w, PH)


def dec(cid, label, x, w=170):
    p.step(cid, label, x, CY - DH // 2, DEC, w, DH)


box("start", "메시지 수신", 40, 120, START)
dec("d1", "JWT 검증 통과?", 220)
dec("d2", "메시지인가?", 450)
box("ctx", "컨텍스트 구성", 680, 170)
box("llm", "LLM 호출", 910, 150)
dec("d3", "도구 호출?", 1120)
box("send", "답변 전송", 1350, 150)
box("save", "대화 기억 저장", 1560, 170)
box("end", "종료", 1790, 120, END)

box("r1", "401 응답", 230, 150, END, CY2)
box("r2", "무시", 460, 150, END, CY2)
box("tool", "도구 실행", 1130, 150, PROC, CY2)

p.edge("e1", "", "start", "d1")
p.edge("e2", "예", "d1", "d2")
p.edge("e3", "아니오", "d1", "r1")
p.edge("e4", "예", "d2", "ctx")
p.edge("e5", "아니오", "d2", "r2")
p.edge("e6", "", "ctx", "llm")
p.edge("e7", "", "llm", "d3")
p.edge("e8", "아니오", "d3", "send")
p.edge("e9", "예", "d3", "tool")
p.edge("e10", "결과 반영", "tool", "llm", dashed=True)
p.edge("e11", "", "send", "save")
p.edge("e12", "", "save", "end")

d.save(os.path.join(HERE, "flow.drawio"))

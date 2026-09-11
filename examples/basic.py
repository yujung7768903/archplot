#!/usr/bin/env python3
"""좌표를 직접 지정하는 기본 예시. 노드 6 · 엣지 6 · 경계 2.

  python3 examples/basic.py
  python3 scripts/drawio_render.py examples/basic.drawio

설치 위치에 무관하게 돌도록 스킬 자신의 scripts 를 상대경로로 잡는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from drawio_build import Diagram, icon  # noqa: E402

d = Diagram("주문 처리 흐름")

# 경계는 노드보다 먼저 판다. 박스는 내용에 맞춰 줄인다.
d.group("g_edge", "퍼블릭 서브넷", 200, 80, 260, 200, kind="subnet")
d.group("g_app", "프라이빗 서브넷", 520, 80, 600, 200, kind="subnet")

# 액터는 모든 경계 밖 끝단. 엣지 라벨을 붙이지 않는다.
d.node("actor", "이용자", 40, 150, icon("onprem/client/user"))
d.node("alb", "ALB", 280, 150, icon("aws/network/elastic-load-balancing"))
d.node("api", "주문 API", 580, 150, icon("aws/compute/ec2"))
d.node("q", "주문 큐", 800, 150, icon("aws/integration/simple-queue-service-sqs"))
d.node("db", "주문 DB", 1020, 150, icon("aws/database/aurora"))
d.node("obj", "영수증 보관", 800, 340, icon("aws/storage/simple-storage-service-s3"))

# exit/entry 를 반드시 준다. 안 주면 draw.io 가 임의로 붙여 캡션을 덮는다.
d.edge("e1", "", "actor", "alb", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e2", "HTTPS", "alb", "api", exit=(1, 0.5), entry=(0, 0.5),
       label_offset=(0, -14))
d.edge("e3", "적재", "api", "q", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e4", "저장", "q", "db", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e5", "업로드", "q", "obj", exit=(0.5, 1), entry=(0.5, 0))
# 되돌아오는 선은 파선으로 성격을 구분하고, 라벨을 겹치지 않게 옮긴다.
# 박스 위로 넘기면 서브넷 라벨을 관통한다. 라벨 아래·아이콘 위의 통로(y=124)로 돌린다.
d.edge("e6", "처리 결과", "db", "api", exit=(0.5, 0), entry=(0.5, 0), dashed=True,
       waypoints=[(1059, 124), (619, 124)], label_pos=0, label_offset=(0, -12))

d.save(os.path.join(HERE, "basic.drawio"))

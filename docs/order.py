#!/usr/bin/env python3
"""README 상단 그림 — 주문 처리 흐름. 연결은 라우터가 정한다.

  python3 docs/order.py
  python3 scripts/drawio_render.py docs/order.drawio

docs/gateway.png 는 examples/routed.py 의 산출물을 복사한 것이다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from drawio_build import Diagram, icon  # noqa: E402
from drawio_route import Panel  # noqa: E402

d = Diagram("주문 처리 흐름")
p = Panel(d, "o", 0, 0)

p.group("g_pub", "퍼블릭 서브넷", 200, 60, 240, 200, kind="subnet")
p.group("g_app", "프라이빗 서브넷", 500, 60, 680, 400, kind="subnet")

p.node("actor", "이용자", 40, 140, icon("aws/general/user"))
p.node("alb", "ALB", 280, 140, icon("aws/network/elastic-load-balancing"))
p.node("api", "주문 API", 560, 140, icon("aws/compute/ec2"))
p.node("q", "주문 큐", 820, 140, icon("aws/integration/simple-queue-service-sqs"))
p.node("worker", "영수증 발행", 1060, 140, icon("aws/compute/lambda"))
p.node("db", "주문 DB", 690, 340, icon("aws/database/aurora"))
# S3 는 VPC 밖 리전 서비스라 서브넷 바깥에 둔다.
p.node("obj", "영수증 보관", 1280, 140, icon("aws/storage/simple-storage-service-s3"))

p.edge("e1", "", "actor", "alb")
p.edge("e2", "HTTPS", "alb", "api")
p.edge("e3", "적재", "api", "q", sp=(1, 0.25), ep=(0, 0.25))
# 아래로 가는 선은 옆면으로 나가 위로 들어간다 — 아래 면으로 내리면 캡션을 관통한다.
p.edge("e4", "저장", "api", "db", sp=(1, 0.75), ep=(0.5, 0))
p.edge("e5", "소비", "q", "worker")
p.edge("e6", "업로드", "worker", "obj")

d.save(os.path.join(HERE, "order.drawio"))

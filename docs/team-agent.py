#!/usr/bin/env python3
"""README 아키텍처 예시 — 팀 에이전트(Claude Agent SDK 자체 호스팅). 연결은 라우터가 정한다.

  python3 docs/team-agent.py
  python3 scripts/drawio_render.py docs/team-agent.drawio

캡션이 아이콘보다 넓으면 아래 면으로 선을 못 낸다(캡션 관통). 아래로 선을 내는
노드(큐·워커·도구)는 캡션을 짧게 두고, 무엇인지는 그룹 라벨과 제목에 적는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from drawio_build import Diagram, icon  # noqa: E402
from drawio_route import Panel  # noqa: E402

TITLE = ("text;html=0;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
         "fontSize=18;fontStyle=1;fontColor=#232F3E;")

d = Diagram("팀 에이전트")
p = Panel(d, "t", 0, 0)

p.node("title", "팀 에이전트 — Claude Agent SDK 를 ECS Fargate 에 자체 호스팅", 40, 0, TITLE,
       w=900, h=40)
p.group("g_ms", "Microsoft Azure", 200, 60, 240, 200, kind="onpremise")
p.group("g_board", "사내 문의 채널", 800, 60, 240, 200, kind="onpremise")
p.group("g_aws", "에이전트 AWS 계정", 440, 320, 1260, 660, kind="cloud")
p.group("g_vpc", "VPC (프라이빗 서브넷)", 900, 560, 560, 400, kind="vpc")
p.group("g_int", "사내 시스템", 1000, 1040, 260, 180, kind="onpremise")
p.group("g_ext", "외부 SaaS", 1300, 1040, 220, 180, kind="account")

p.node("actor", "담당자", 40, 140, icon("aws/general/user"))
p.node("bot", "Teams 봇", 260, 140, icon("azure/ml/bot-services"))
p.node("board", "게시판", 880, 140, icon("aws/general/forums"))

p.node("apigw", "API Gateway", 680, 420, icon("aws/network/api-gateway"))
p.node("recv", "수신 Lambda", 900, 420, icon("aws/compute/lambda"))
p.node("q", "SQS", 1120, 420, icon("aws/integration/simple-queue-service-sqs"))
p.node("dynamo", "세션 저장소", 700, 640, icon("aws/database/dynamodb"))
p.node("worker", "워커", 1120, 640, icon("aws/compute/fargate"))
p.node("plink", "VPC 엔드포인트", 1340, 640, icon("aws/network/privatelink"))
p.node("model", "Bedrock", 1580, 640, icon("aws/ml/bedrock"))
p.node("tools", "도구", 1120, 840, icon("aws/compute/elastic-container-service"))
p.node("db", "사내 DB", 1120, 1100, icon("aws/database/aurora"))
p.node("jira", "Jira", 1380, 1100, icon("saas/saas"))

p.edge("e1", "", "actor", "bot")
p.edge("e2", "HTTPS", "bot", "apigw", sp=(1, 0.25), ep=(0.25, 0))
p.edge("e3", "문의 등록", "board", "apigw", sp=(0, 0.75), ep=(0.75, 0))
p.edge("e4", "", "apigw", "recv")
p.edge("e5", "적재", "recv", "q")
p.edge("e6", "폴링", "q", "worker", sp=(0.25, 1), ep=(0.25, 0))
p.edge("e7", "세션", "worker", "dynamo")
p.edge("e8", "추론", "worker", "plink")
p.edge("e9", "", "plink", "model")
p.edge("e10", "MCP", "worker", "tools", sp=(0.25, 1), ep=(0.25, 0))
p.edge("e11", "읽기 전용", "tools", "db", sp=(0.25, 1), ep=(0.25, 0))
p.edge("e12", "조회·등록", "tools", "jira", sp=(1, 0.5), ep=(0.5, 0))

d.save(os.path.join(HERE, "team-agent.drawio"))

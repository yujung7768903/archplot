#!/usr/bin/env python3
"""README 아키텍처 예시 — 팀 에이전트(Claude Agent SDK 자체 호스팅). 연결은 라우터가 정한다.

  python3 docs/team-agent.py
  python3 scripts/drawio_render.py docs/team-agent.drawio
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from drawio_build import Diagram, icon  # noqa: E402
from drawio_route import Panel  # noqa: E402

ROLE = ("text;html=0;strokeColor=none;fillColor=none;align=center;verticalAlign=top;"
        "fontSize=12;fontColor=#232F3E;")
ROW1, ROW2 = 480, 680
C1, C2, C3, C4, C5 = 300, 540, 780, 1020, 1240

d = Diagram("팀 에이전트")
p = Panel(d, "a", 0, 0)


def pair(cid, col, row, ic, service, role, role_w=158):
    """아이콘 캡션에 서비스명, 그 아래 한 줄로 역할."""
    p.node(cid, service, col, row, icon(ic))
    p.node(cid + "_role", role, col - (role_w - 78) // 2, row + 100, ROLE, w=role_w, h=20)


p.group("g_m365", "Microsoft 365 / Azure", 200, 60, 620, 220, kind="onpremise")
p.group("g_board", "문의 게시판", 880, 60, 240, 220, kind="onpremise")
p.group("g_aws", "사내 AWS 계정", 200, 380, 1300, 470, kind="cloud")
# API Gateway 는 리전 서비스라 VPC 밖. VPC 라벨이 위에서 내려오는 두 선을 피한다.
p.group("g_vpc", "VPC (프라이빗 서브넷)", 480, 420, 660, 400, kind="vpc")
p.group("g_ext", "외부 SaaS", 1060, 920, 240, 170, kind="account")
p.group("g_int", "사내 시스템", 1340, 920, 240, 170, kind="onpremise")

p.node("actor", "담당자", 40, ROW1, icon("aws/general/user"))
p.node("teams", "Teams", 260, 140, icon("saas/chat/teams"))
p.node("bot", "Azure Bot Service", 480, 140, icon("azure/ml/bot-services"))
p.node("entra", "Entra 앱 등록", 700, 140, icon("azure/identity/azure-active-directory"))
# 아래로 선을 내는 노드라 캡션을 비우고 이름은 그룹 라벨에 둔다.
p.node("board", "", 940, 140, icon("aws/general/forums"))
p.node("apigw", "API Gateway", 340, ROW1, icon("aws/network/api-gateway"))
pair("bf", C2, ROW1, "aws/compute/lambda", "Lambda", "Bot Framework 어댑터", role_w=180)
p.node("rt", "Claude Agent SDK (Fargate)", C3, ROW1, icon("aws/compute/fargate"))
p.node("plink", "VPC 엔드포인트", C4, ROW1, icon("aws/network/privatelink"))
p.node("model", "Bedrock (Claude)", C5, ROW1, icon("aws/ml/bedrock"))
# 아래 줄은 반 칸씩 엇갈려 둔다 — 위 노드 옆면에서 나와 아래 노드 위로 들어간다.
pair("store", 640, ROW2, "aws/database/dynamodb", "DynamoDB", "세션 · 대화 기록", role_w=160)
p.node("tool", "ECS (MCP 도구)", 900, ROW2, icon("aws/compute/elastic-container-service"))
p.node("jira", "Jira·Confluence", 1180, 980, icon("saas/saas"))
p.node("db", "사내 DB", 1420, 980, icon("aws/general/generic-database"))

p.edge("f1", "", "actor", "teams")
p.edge("f2", "문의·승인 메시지", "teams", "bot")
p.edge("f3", "앱 권한 토큰", "bot", "entra", dashed=True)
p.edge("f4", "아웃바운드 HTTPS", "bot", "apigw", sp=(0, 0.75), ep=(0.75, 0))
p.edge("f5", "문의 등록", "board", "apigw", sp=(0.25, 1), ep=(0.25, 0))
p.edge("a1", "요청 변환", "apigw", "bf")
p.edge("a2", "세션 시작·재개", "bf", "rt")
p.edge("a3", "추론 호출", "rt", "plink")
p.edge("a4", "", "plink", "model")
p.edge("a5", "세션 체크포인트", "rt", "store", sp=(0, 0.75), ep=(0.5, 0))
p.edge("a6", "도구 호출", "rt", "tool", sp=(1, 0.75), ep=(0.5, 0))
p.edge("t1", "조회·등록", "tool", "jira", sp=(1, 0.75), ep=(0.5, 0))
p.edge("t2", "조회", "tool", "db", sp=(1, 0.25), ep=(0.5, 0))

d.save(os.path.join(HERE, "team-agent.drawio"))

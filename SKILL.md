---
name: archplot
description: 아키텍처·구성도·다이어그램을 그릴 때 쓴다. draw.io(.drawio) 를 코드로 생성하고 PNG 로 렌더한다. "아키텍처 그려줘", "구성도 그려줘", "다이어그램 만들어줘", "인프라 도식화", "시스템 구조 그려줘", "이 흐름 그림으로 정리해줘", 계정·리전·VPC 경계를 박스로 나눠야 하는 그림, 첨부한 아키텍처 이미지를 비슷하게 재현해달라는 요청에 해당한다. 클라우드 공식 아이콘(AWS·GCP·Azure·K8s)뿐 아니라 사내 서비스·온프레미스 구성도에도 쓴다. 문서 본문에 인라인으로 박아 넣을 시퀀스도·상태도는 design-doc-mermaid 를 쓴다.
---

# draw.io 아키텍처 다이어그램

`.drawio` 를 파이썬으로 생성하고 헤드리스 Chromium 이 PNG 로 렌더한다. **좌표를 직접 지정한다** — 자동 배치로는 라벨 겹침과 빈 여백을 없앨 수 없다.

아이콘은 `diagrams` 패키지가 번들한 클라우드 공식 아이콘 PNG(라운드 코너·그라데이션)를 data URI 로 심는다. draw.io 자체 도형은 경계 박스에만 쓴다.

## 절차

| 단계 | 명령 | 확인 |
| --- | --- | --- |
| 1. 생성기 작성 | `<이름>.py` 에 노드·엣지를 좌표와 함께 선언 | — |
| 2. `.drawio` 생성 | `python3 <이름>.py` | 셀 개수 출력 |
| 3. PNG 렌더 | `python3 ~/.claude/skills/archplot/scripts/drawio_render.py <이름>.drawio` | 캔버스 크기 출력 |
| 4. 눈으로 확인 | Read 툴로 PNG 를 연다 | 겹침·잘림·꼬임은 실행 성공만으로 안 드러난다 |
| 4-1. 확대 확인 | `python3 ~/.claude/skills/archplot/scripts/drawio_crop.py <이름>.png <x> <y> <w> <h> --zoom 2` | **전체 1장으로 끝내지 않는다.** 축소하면 1.2px 선이 글자 획으로 보여 라벨 관통이 안 드러난다. 그룹 박스 좌상단(라벨)과 긴 캡션 주변을 개별로 확대한다 |
| 5. 발행 (요청받았을 때만) | `python3 ~/.claude/skills/archplot/scripts/confluence_publish.py <이름>.png --page <id>` | `md5 일치` 출력 |

어긋나면 생성기의 좌표를 고쳐 2번부터 다시 돈다. PNG 도 `.drawio` 도 손으로 편집하지 않는다 — 정본은 생성기 하나다.

`.py` 와 산출물은 같은 디렉토리에 남긴다. 임시 디렉토리에 두지 않는다.

## 생성기 작성

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/archplot/scripts"))
from drawio_build import Diagram, icon

d = Diagram("제목")

d.group("g1", "운영 계정", 200, 80, 400, 200)              # 경계는 노드보다 먼저
d.group("g2", "서비스 계정", 200, 360, 900, 230)

d.node("actor", "담당자", 40, 140, icon("onprem/client/user"))   # 액터는 경계 밖
d.node("api", "API", 260, 140, icon("aws/compute/ec2"))
d.node("db",  "DB",  480, 140, icon("aws/database/aurora"))

d.edge("e1", "", "actor", "api", exit=(1, 0.5), entry=(0, 0.5))  # 액터 엣지는 무라벨
d.edge("e2", "저장", "api", "db", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e3", "콜백", "db", "api", exit=(0.5, 0), entry=(1, 0.85), dashed=True,
       waypoints=[(519, 40), (368, 40)], label_pos=0, label_offset=(0, -12))

d.save("out.drawio")
```

전체 예시는 `examples/basic.py` (노드 6 · 엣지 6 · 경계 2). 그대로 돌리면 `.drawio` 와 PNG 가 나온다.

### 좌표 규칙

- 노드는 78×78. 좌표는 20px 격자에 맞춘다.
- 캡션이 한 줄이면 행 간격 160px·열 간격 200px 로 시작한다. 캡션이 3~5줄 섞이면 행 220px·열 240~300px 가 필요하다. 좁으면 캡션끼리 붙고 세로선이 지날 열이 없어진다.
- 같은 행은 y 를 맞추고, 열 간격을 균일하게 둔다 (모범 도면 4/4).
- 흐름 주축을 하나 정한다 (좌→우 또는 위→아래). 되돌아오는 선은 파선으로 성격을 구분한다.
- 경계 박스는 내용에 맞춰 줄인다. 남은 빈 공간은 그림이 미완성처럼 보인다.
- **박스 안쪽 여백은 최소 20px, 라벨이 있는 변은 40px.** 내용이 경계선에 붙으면 묶은 것으로
  안 읽힌다. 20px 은 격자 한 칸이고, 라벨 줄은 fontSize 12 기준 24px 를 먹어 20px 로는 첫 줄을 문다.

### 엣지 제어

엣지가 10개를 넘거나 조건 마름모가 섞이면 아래 인자를 손으로 맞추지 않는다 — **배선 라우터** 절의 `Panel` 을 쓴다.

| 하고 싶은 것 | 인자 |
| --- | --- |
| 선이 노드의 어디에 붙을지 | `exit=(x, y)`, `entry=(x, y)` — 0~1 비율. **반드시 준다.** 안 주면 draw.io 가 임의로 붙여 캡션을 덮는다 |
| 우회 경로 | `waypoints=[(x, y), ...]` |
| 같은 두 노드를 오가는 선 2본의 라벨 분리 | `label_pos`(-1~1), `label_offset=(dx, dy)` |
| 평행선 간격이 라벨 폭보다 좁을 때 | `label_offset=(dx, dy)` 로 선에서 떼어 놓는다. `label_pos` 는 선 위에서만 움직여서 못 푼다. 라우터의 `Panel.edge` 도 이 인자를 받는다 |
| 부가 흐름(콜백·인증·비동기) | `dashed=True` |

**한 노드의 한쪽 면에 선을 3개 이상 붙이지 않는다.** 캡션이 아이콘 아래에 있어 하단에 몰면 가려진다. 좌·우·상으로 분산한다.

**캡션이 아이콘(78px)보다 넓은 노드는 아래 변을 아예 쓰지 않는다.** 캡션은 아이콘 아래 가운데
정렬로 그려지고 폭 제한이 없다. 아래 변에서 나간 선은 그 글자를 세로로 관통한다. 역할 캡션을
두 줄 이상 다는 도면에서는 거의 모든 노드가 여기 해당하므로, 아래 두 패턴으로 통일하는 게 빠르다.

| 흐름 | 패턴 |
| --- | --- |
| 내려가는 흐름 | 출발 노드의 **옆 변**으로 나가 → 대상의 **위 변**으로 들어간다 |
| 올라가는 흐름 | 출발 노드의 **위 변**으로 나가 → 대상의 **옆 변**으로 들어간다 |

그러면 "어느 노드의 어느 변을 비워 둘지"가 배치를 결정한다. 위로 올라가는 선을 받아야 하는
노드는 그 행의 끝(왼쪽 또는 오른쪽)에 두어 옆 변을 비운다.

### 아이콘

이름을 모르면 검색한다. 추측하면 `FileNotFoundError` 로 바로 걸린다.

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/skills/archplot/scripts')
from drawio_build import find_icon; print(find_icon('mediaconvert'))"
```

`aws` 외에 `gcp` `azure` `k8s` `onprem` `saas` `generic` `programming` `elastic` `firebase` `alibabacloud` `oci` `ibm` `digitalocean` `openstack` `outscale` `gis` 가 있다.

### 경계 종류

`d.group(..., kind=)` 에 넣는다. 테두리 색·파선 여부는 draw.io 정의를 따른다.

| `kind` | 용도 |
| --- | --- |
| `account` (기본) | 계정 경계 |
| `cloud` | AWS Cloud 전체 |
| `region` | 리전 |
| `vpc` | VPC |
| `subnet` | 서브넷 |
| `autoscaling` | Auto Scaling 그룹 |
| `onpremise` | 온프레미스·사내 데이터센터 |

경계마다 하나씩 판다. 중첩은 계정 > 리전 > VPC > 서브넷 순으로 쌓는다.

## 배선 라우터 (`scripts/drawio_route.py`)

노드가 다 놓인 뒤(`save()` 시점) 연결점과 직교 경로를 계산해 웨이포인트로 박는다. `exit`/`entry`/`waypoints` 를 손으로 안 준다.

```python
from drawio_build import Diagram, icon
from drawio_route import Panel, beside

DIAMOND = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D86613;fontSize=11;"

d = Diagram("제목")
p = Panel(d, "a", 0, 0)                            # id 접두사 · 좌표 오프셋 — 한 장에 시안 여러 개
p.group("g_vpc", "VPC", 200, 60, 700, 260, kind="vpc")
p.step("q", "허용?", 420, 140, DIAMOND, 190, 58)    # 흐름 칸·조건 마름모. 선이 관통하지 못하는 도형
p.node("api", "API", 260, beside(p, "q"), icon("aws/compute/ec2"))       # 마름모 옆 아이콘은
p.node("db", "DB", 720, beside(p, "q"), icon("aws/database/aurora"))     # 세로 중심을 맞춘다
p.edge("e1", "도구 호출", "api", "q")                # 연결점·경로는 라우터가 정한다 → 왼쪽 꼭짓점, 직선
p.edge("e2", "허용분만", "q", "db")                  # 오른쪽 꼭짓점 → 직선
d.save("out.drawio")
```

| 규칙 | 이유 |
| --- | --- |
| 아이콘은 각 변 3개씩 12개 연결점만. 모서리는 안 쓴다 | 모서리에서 나간 선은 아이콘에서 떠 보인다 |
| 마름모는 꼭짓점 4 + 빗변 중앙 4 만. 빗변 중앙은 `(x, y, "h"\|"v")` 로 나가는 방향까지 정한다 | 경계상자 변 위의 `(1, 0.75)` 는 마름모 둘레 밖이라 draw.io 가 빗변으로 투영해 첫 구간이 대각선이 된다 |
| 그룹 경계·그 밖의 도형은 변 중앙 4개. 그룹도 엣지 끝점이 된다 | 서브넷 전체가 보내는 선 |
| 직선 → L → Z → 우회 순. 두 연결점이 같은 x·y 면 직선 | 꺾임은 정보가 아니다 |
| **첫 구간은 연결점이 난 면 쪽으로 나가야 한다.** 옆 변으로 나가려면 대상이 그 옆에, 위·아래 변으로 나가려면 대상이 그 위·아래에 있어야 한다. 들어가는 쪽도 같다 | 아니면 첫 구간이 노드 안으로 파고든다. 이 조건에 걸리면 `RuntimeError` 인데 메시지가 "장애물" 과 "방향 규칙 위반" 을 구분해 주지 않는다 — 먼저 이 표를 의심하라 |
| **그룹 라벨·노드 캡션 글자를 지나면 경고**가 나온다. 버리지는 않는다 | 피할 배치가 없는 경우가 있어서다. 경고가 나오면 그 열을 비우도록 노드·박스를 옮겨라. **축소한 PNG 로는 라벨 관통이 거의 안 보인다** |
| 마름모 옆 아이콘은 `beside(p, cid)` 로 세로 중심을 맞춘다 | 10px 어긋나면 4.5px 잔꺾임이 생긴다 |
| 들어오는 점은 겹치지 않는다. 한 꼭짓점에 들어오는 선과 나가는 선이 겹치면 들어오는 쪽을 `ep=(0.75, 0.25, "h")` 처럼 빗변 중앙에 못박는다 | 나가는 선이 꼭짓점을 잃으면 대각선이 된다 |
| `off=` 는 Z 의 중간선 위치. 임의 값을 받는다. 가로→세로→가로면 `mx=(ax+bx)/2+off`, 세로→가로→세로면 `my=(ay+by)/2+off` — 직선·L 에는 `0` 만 받는다 | 라우터는 그룹 경계선을 장애물로 안 봐서 박스 안을 훑는 경로를 스스로 못 피한다 |
| 꺾인 경로의 직선 구간은 `MIN_SEG`(24px) 이상. 못 지키면 stderr 경고 | 짧은 구간은 잔꺾임으로 보여 선이 노드에 붙은 듯 읽힌다. 경고가 나면 두 노드 간격을 벌린다 |
| 경로가 없으면 `RuntimeError` | 배치를 고치라는 신호다. 조용히 대각선을 그리지 않는다 |

import 하면 엣지 스타일이 `edgeStyle=none`(웨이포인트를 곧이곧대로 그림) · 라벨 배경 흰색으로 바뀐다. `lp=` 로 라벨 위치(-1~1)를 옮긴다. 전체 예시는 `examples/routed.py` (아이콘 5 · 마름모 1 · 엣지 6 · 경계 2). 마름모와 아이콘은 연결점 격자가 다르고, 캡션은 아이콘 아래에 있다 — 그 둘을 피한 배치를 주석으로 적어 두었다.

## 작도 규칙

AWS 가 공개한 레퍼런스 아키텍처 도면 4장을 대조해 정한 것이다. 어길 근거가 없으면 따른다.
오른쪽 `관찰` 열의 `4/4` 는 그 4장 모두에서 지켜진 것, `3/4` 는 3장에서 지켜진 것을 뜻한다.
(원본 이미지는 저작권자가 따로 있어 이 저장소에 넣지 않는다. AWS Architecture Center 에서 볼 수 있다.)

| 규칙 | 관찰 |
| --- | --- |
| 곡선 금지. 90° 직교 꺾인선만 | 4/4 |
| 엣지 라벨은 1~3단어 (데이터 종류·프로토콜·단일 동작어) | 4/4 |
| **하나의 자원은 하나의 노드.** prefix 가 달라도 같은 버킷이면 노드 1개 | 규칙 |
| 노드 라벨 = 서비스명 (+ 괄호 역할). 캡션은 아이콘 아래 최대 2줄 | 4/4 |
| 액터는 1종만, 모든 경계 밖 끝단, 엣지 라벨 없음 | 3/4 |
| 범례 없음. 선 종류가 2가지여도 안 만든다 | 4/4 |
| 흐름과 무관한 자원(IAM·CloudWatch)은 엣지 없이 여백에 두거나 뺀다 | 3/4 |
| **아이콘이 있는 것만 노드가 된다** | 4/4 |
| 벤더 아이콘은 종횡비·색을 바꾸지 않는다. 크기를 줄여도 가로세로 비율은 유지한다 | 각 벤더 상표 가이드라인이 요구하는 사항 |

마지막 항목이 층위를 지키는 유일한 장치다. 프로토콜·동작은 아이콘이 없으니 엣지 라벨로 밀려나고, 함수·필드·경로는 아이콘도 엣지도 못 얻어 그림에서 탈락한다.

예외는 **AZ 별 복제본**뿐이다. `MySQL (Master)` / `MySQL (Slave)`, AZ 마다 있는 인스턴스는 서로 다른 자원이므로 별개 노드가 맞다.

### 그림에 넣지 말 것

| 금지 | 대신 |
| --- | --- |
| 스토리지 경로·prefix·키 패턴·파일명 | 버킷·큐 이름까지만 |
| HTTP 메서드·URL 경로·쿼리 파라미터·페이로드 필드명 | `인코딩 옵션` 같은 1~3단어. 경로는 문서 본문으로 |
| 엣지에 ①②③ 순서번호 | 화살표 방향으로 순서가 읽히게 배치. 모범 도면 4장 중 엣지 번호를 쓴 것은 0장 |
| IAM 역할 ARN·STS AssumeRole 화살표 | 아예 뺀다 |
| 에러 경로·재시도·타임아웃·DLQ | 정상 경로 1개만 |
| 함수명·핸들러명·테이블 컬럼 | 서비스명 + 역할 |

## 흔한 실패

| 증상 | 원인 | 조치 |
| --- | --- | --- |
| `FileNotFoundError: 아이콘 없음` | 아이콘 경로 추측 | `find_icon()` 으로 검색 |
| 아이콘 자리가 빈 사각형 | draw.io 자체 도형 이름을 잘못 씀 | `icon()` 을 쓴다. draw.io 도형은 경계에만 |
| 캡션이 선에 가림 | 한 면에 선을 3개 이상 붙였다 | `exit`/`entry` 를 다른 면으로 분산 |
| 라벨 두 개가 겹쳐 뭉개짐 | 같은 두 노드를 오가는 선 2본 | 한쪽에 `label_pos`·`label_offset` |
| 경계선·캡션이 이미지 끝에서 잘림 | 캔버스 여백 부족 | `drawio_render.py` 의 `PAD` 상수 |
| `글자를 지난다` 경고 | 세로선 열이 그룹 라벨 띠나 다른 노드 캡션과 겹친다 | 그 열을 비운다. 그룹 라벨은 좌상단 고정이라 박스 안 왼쪽 열은 쓸 수 없다 — 회랑을 박스 **밖**으로 빼라 |
| `RuntimeError: 직교 경로가 없다` | 장애물이 아니라 **방향 규칙 위반**인 경우가 많다 | 위 "경로 형태 허용 규칙" 을 먼저 본다. `sp`/`ep` 를 반대쪽 면으로 바꾸거나 노드를 옮긴다 |
| 렌더는 됐는데 아이콘만 안 나옴 | AWS4 스텐실을 CDN 에서 받아온다 | 네트워크 확인 |
| Confluence 첨부 버전이 안 올라감 | 같은 파일명으로 `POST /child/attachment` 재호출 | `confluence_publish.py` 를 쓴다 (내부에서 `/{id}/data` 로 보낸다) |

## 스크립트

| 파일 | 역할 |
| --- | --- |
| `scripts/drawio_build.py` | `.drawio` 생성. `Diagram`, `icon()`, `find_icon()`. `python3 drawio_build.py` 로 자체 점검 |
| `scripts/drawio_route.py` | 엣지 배선. `Panel`, `beside()`. 연결점·직교 경로·관통 판정을 계산해 웨이포인트로 박는다. `python3 drawio_route.py` 로 자체 점검 |
| `scripts/drawio_render.py` | `.drawio` → PNG. 헤드리스 Chromium + `vendor/viewer-static.min.js`. `--scale` 기본 2배 |
| `scripts/drawio_crop.py` | PNG 일부 확대. 라벨 관통 검수용 |
| `scripts/confluence_publish.py` | PNG 를 페이지에 첨부. 새 페이지 생성도 가능. md5 로 검증 |
| `vendor/viewer-static.min.js` | draw.io viewer. drawio Desktop·xvfb 불필요 |
| `examples/basic.py` | 좌표 직접 지정 예시. 돌려서 산출물을 만든다 (저장소에 산출물은 없다) |
| `examples/routed.py` | 배선 라우터 예시. `Panel` · `step` · `beside` · `sp`/`ep` 차선 |

Chromium 은 `~/.cache/ms-playwright` 또는 `~/.cache/puppeteer` 의 것을 자동으로 찾는다. drawio Desktop CLI 는 WSL 에서 export 모드가 멈추므로 쓰지 않는다.

## 다른 다이어그램 도구와의 구분

| 요청 | 도구 |
| --- | --- |
| 클라우드 공식 아이콘, 계정·리전·VPC 경계 | 이 스킬 |
| 문서에 박아 넣을 흐름도·시퀀스·상태도 | `design-doc-mermaid` (Confluence·GitHub 에서 그대로 렌더) |
| 다크테마 SVG, 클라우드 아닌 개념도 | `baoyu-diagram` |

픽셀 단위로 통제해야 하면 draw.io 앱을 직접 열어 그린다.

# archplot

[English](README.md) | 한국어 | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

아키텍처 다이어그램을 코드로 그리는 Claude Code 스킬이다. 노드·경계·엣지를 **명시적인 좌표로**
선언하는 작은 Python 생성기를 작성하고, 그것을 실행해 `.drawio` 파일을 만든 뒤, headless
Chromium 과 함께 번들된 draw.io 뷰어로 PNG 를 렌더한다 — draw.io Desktop 도, `xvfb` 도,
`sudo` 도 필요 없다.

클라우드 벤더 아이콘은 [`diagrams`](https://github.com/mingrammer/diagrams) 패키지가 번들한
공식 아이콘 PNG 에서 가져오며, base64 data URI 로 `.drawio` 파일에 직접 삽입되므로 파일 하나로
자족적이다. draw.io 자체 도형은 경계 박스(계정·리전·VPC·서브넷)에만 쓴다.

> [!NOTE]
> 좌표를 손으로 지정하는 것은 의도한 설계다. 자동 배치는 라벨 겹침과 빈 여백을 없애지 못하므로,
> 이 스킬은 배치 자동화를 포기하는 대신 캔버스에 대한 완전한 통제를 택했다. 자동화한 것은 기계적인
> 부분, 즉 엣지 라우팅이다.

## 특징

- **직접 통제하는 좌표** — 20px 그리드 위의 78x78 아이콘 노드, 내용물에 맞춰 크기를 잡은 경계 박스.
- **Orthogonal 엣지 라우터** — 모든 노드를 배치한 뒤, 라우터가 연결점을 고르고 90도 경로를 계산해
  waypoint 로 고정한다. 직선을 먼저 시도하고, 그다음 L, Z, 우회 경로 순으로 시도한다. 유효한 경로가
  없으면 대각선을 조용히 그리는 대신 `RuntimeError` 를 낸다. 아이콘, 흐름 단계, 그룹 라벨과 노드
  캡션의 텍스트 박스가 모두 장애물로 계산된다.
- **17개 계열에 걸친 2,440개 벤더 아이콘** (작성 시점의 `diagrams` 번들 기준) — `aws`, `gcp`,
  `azure`, `k8s`, `onprem`,
  `saas`, `generic`, `programming`, `elastic`, `firebase`, `alibabacloud`, `oci`, `ibm`,
  `digitalocean`, `openstack`, `outscale`, `gis`.
- **Chromium 이 도는 곳이면 어디서든 렌더** — draw.io 뷰어를 벤더링했으므로 렌더링에 GUI 도 데스크톱
  앱도 필요 없다. draw.io Desktop CLI 의 export 모드가 WSL 에서 멈추기 때문에 이렇게 작성했다.
- **에이전트를 위한 작도 규칙** — `SKILL.md` 에 AWS 레퍼런스 아키텍처 다이어그램 4장을 비교해 도출한
  규칙 집합이 들어 있어, 에이전트가 즉흥적으로 그리지 않고 일관되게 그린다.
- **선택적인 Confluence 게시** — 렌더한 PNG 를 페이지에 첨부하고 md5 로 검증한다.

## 시작하기

### 요구사항

| 요구사항 | 비고 |
| --- | --- |
| Python 3 | 표준 라이브러리만 사용. 추가 런타임 의존성 없음 |
| `pip install diagrams` | 생성기가 읽는 벤더 아이콘 PNG 를 제공 |
| Chromium | `~/.cache/ms-playwright` 또는 `~/.cache/puppeteer` 에서 자동 탐지, 없으면 시스템의 `chromium` / `chromium-browser` / `google-chrome` |
| Confluence 게시 (선택) | 환경변수 `CONFLUENCE_SITE`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` 필요 |

### 설치

```bash
npx skills add yujung7768903/archplot
```

### 검증

두 스크립트 모두 자체 점검을 제공한다.

```bash
python3 scripts/drawio_build.py    # demo OK
python3 scripts/drawio_route.py    # drawio_route: ok
```

## 어떻게 동작하는가

생성기 `.py` 가 유일한 원본이다. `.drawio` 와 PNG 는 빌드 산출물이며 절대 손으로 고치지 않는다 —
무언가 이상해 보이면 좌표를 고쳐 2단계부터 다시 실행한다.

| 단계 | 명령 | 확인 방법 |
| --- | --- | --- |
| 1. 생성기 작성 | `<name>.py` 에 노드·경계·엣지를 좌표와 함께 선언 | — |
| 2. `.drawio` 빌드 | `python3 <name>.py` | 경계 수와 셀 수를 출력 |
| 3. PNG 렌더 | `python3 ~/.claude/skills/archplot/scripts/drawio_render.py <name>.drawio` | 캔버스 크기를 출력 |
| 4. PNG 보기 | 이미지를 연다 | 겹침·잘림·교차한 엣지는 종료 코드에 나타나지 않는다 |
| 4-1. 확대 | `python3 ~/.claude/skills/archplot/scripts/drawio_crop.py <name>.png <x> <y> <w> <h> --zoom 2` | 전체 보기 한 번으로는 부족하다 — 축소된 상태에서는 1.2px 선이 글자 획처럼 보이고, 라벨을 관통하는 선은 보이지 않는다. 각 그룹 박스의 좌상단(라벨이 있는 자리)과 긴 캡션 주변을 하나씩 확대한다 |
| 5. 게시 (선택) | `python3 ~/.claude/skills/archplot/scripts/confluence_publish.py <name>.png --page <id>` | md5 일치를 출력 |

## 생성기 작성

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/archplot/scripts"))
from drawio_build import Diagram, icon

d = Diagram("Title")

d.group("g1", "Ops account", 200, 80, 400, 200)          # boundaries before nodes
d.group("g2", "Service account", 200, 360, 900, 230)

d.node("actor", "Operator", 40, 140, icon("onprem/client/user"))   # actors sit outside
d.node("api", "API", 260, 140, icon("aws/compute/ec2"))
d.node("db",  "DB",  480, 140, icon("aws/database/aurora"))

d.edge("e1", "", "actor", "api", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e2", "store", "api", "db", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e3", "callback", "db", "api", exit=(0.5, 0), entry=(1, 0.85), dashed=True,
       waypoints=[(519, 40), (368, 40)], label_pos=0, label_offset=(0, -12))

d.save("out.drawio")
```

스킬에 내장된 배치 지침이다.

- 아이콘 노드는 78x78 이다. 좌표는 20px 그리드에 맞춘다.
- 한 행 안에서 `y` 를 정렬하고 열 간격을 균일하게 유지한다.
- 흐름의 주축을 하나(좌→우 또는 상→하) 고르고, 되돌아오는 경로는 파선으로 한다.
- 경계 박스는 내용물에 맞게 줄인다 — 남는 공간은 미완성으로 읽힌다.
- 박스 안쪽에 최소 20px, 라벨이 있는 변에는 40px 의 여백을 둔다.
- 한 노드의 같은 변에 엣지를 셋 이상 붙이지 않는다. 캡션이 아이콘 아래에 있어 가려진다.
- 캡션은 아이콘 아래에 폭 제한 없이 가운데 정렬로 그려지므로, **캡션이 아이콘(78px)보다 넓은 노드는
  아래쪽 연결점을 쓰면 안 된다** — 그 선이 글자를 세로로 관통한다.
- 대신 흐름을 일관되게 유지한다. 아래로 향하는 흐름은 **옆면**으로 나가 대상의 **위쪽**으로 들어가고,
  위로 향하는 흐름은 **위쪽**으로 나가 대상의 **옆면**으로 들어간다. 위로 오는 선을 받아야 하는 노드는
  옆면이 비도록 행의 끝에 배치한다.
- 간격: 한 줄짜리 캡션이면 행 간격 160px, 열 간격 200px 에서 시작한다. 3~5줄 캡션이 섞여 있으면
  행 220px, 열 240~300px 로 한다.
- `exit` 와 `entry` 는 선택이 아니다. 이것이 없으면 draw.io 가 선을 임의의 위치에 붙이고 캡션 위에
  떨어진다.

## 엣지 라우팅

다이어그램의 엣지가 열 개를 넘거나 판단 마름모가 섞이면, `exit` / `entry` / `waypoints` 를 손으로
지정하는 것을 그만두고 `Panel` 을 쓴다. 라우팅은 `save()` 시점에 계산된다.

```python
from drawio_build import Diagram, icon
from drawio_route import Panel, beside

DIAMOND = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D86613;fontSize=11;"

d = Diagram("Title")
p = Panel(d, "a", 0, 0)                            # id prefix + coordinate offset
p.group("g_vpc", "VPC", 200, 60, 700, 260, kind="vpc")
p.step("q", "Allowed?", 420, 140, DIAMOND, 190, 58)
p.node("api", "API", 260, beside(p, "q"), icon("aws/compute/ec2"))
p.node("db", "DB", 720, beside(p, "q"), icon("aws/database/aurora"))
p.edge("e1", "tool call", "api", "q")              # the router picks points and path
p.edge("e2", "allowed only", "q", "db")
d.save("out.drawio")
```

| 규칙 | 이유 |
| --- | --- |
| 이미지 도형은 연결점 12개를 쓴다 — 변마다 셋, 모서리는 쓰지 않는다 | 모서리에서 나가는 엣지는 아이콘에서 떨어져 보인다 |
| 마름모는 꼭짓점 4개와 빗변 중점 4개만 쓰며, 후자는 나가는 방향을 고정하기 위해 `(x, y, "h"\|"v")` 로 적는다 | `(1, 0.75)` 같은 경계 상자 기준 점은 마름모 외곽선 바깥에 있어 draw.io 가 그것을 빗변에 투영하고, 첫 구간이 대각선이 된다 |
| 경계 그룹과 그 밖의 일반 도형은 변의 중점 4개를 쓰며, 그룹 자체가 엣지의 끝점이 될 수 있다 | 서브넷 전체가 보내는 엣지를 위해서다 |
| 직선, 그다음 L, Z, 우회 순 — 두 점이 x 나 y 를 공유하면 언제나 직선 | 꺾임은 정보가 아니다 |
| 첫 구간은 해당 변이 향한 방향으로 나가야 한다 — 옆면으로 나가려면 대상이 옆에 있어야 하고, 위나 아래로 나가려면 대상이 위나 아래에 있어야 한다. 들어오는 쪽도 같다 | 그러지 않으면 첫 구간이 노드 쪽으로 되꺾인다. 이를 어기면 `RuntimeError` 가 발생하며, 메시지는 "장애물에 막힘" 과 "방향 규칙 위반" 을 구분하지 않는다 — 이 규칙을 먼저 의심한다 |
| 그룹 라벨(박스 좌상단)이나 노드 캡션(아이콘 아래)을 지나는 경로에는 큰 벌점을 준다. 대안이 없으면 그 경로를 유지하고 stderr 로 경고를 낸다 | 그러지 않으면 최단 경로가 글자를 그대로 관통한다. 경고가 나오면 노드나 박스를 옮겨 그 열을 비운다 — 축소된 PNG 에서는 글자를 지나는 선이 거의 보이지 않는다 |
| 마름모 옆의 아이콘은 `beside(p, cid)` 로 정렬한다 | 10px 만 어긋나도 4.5px 짜리 토막 꺾임이 생긴다 |
| 들어오는 점은 다른 어떤 것과도 겹치지 않는다. 나가는 엣지와 충돌하면 빗변 중점(`ep=(0.75, 0.25, "h")`)에 고정한다 | 꼭짓점을 잃은 나가는 엣지는 대각선이 된다 |
| 같은 두 노드 사이의 요청/응답 쌍은 `sp=` / `ep=` 로 차선을 고정한다 | 점수 계산만으로는 어느 선이 위로 갈지 정해지지 않는다 |
| `off=` 는 Z 의 가운데 선을 옮긴다 | 라우터는 그룹 경계를 장애물로 보지 않으므로, 박스를 가로지르는 경로를 스스로 피하지 못한다 |
| 꺾인 경로의 직선 구간은 최소 `MIN_SEG`(24px) 이어야 하며, 그렇지 않으면 stderr 로 경고가 나온다 | 짧은 구간은 토막 꺾임으로 읽힌다. 두 노드 사이를 더 벌린다 |
| 유효한 경로가 없으면 `RuntimeError` 를 낸다 | 조용히 대각선을 그리라는 뜻이 아니라 배치를 고치라는 신호다 |

`drawio_route` 를 import 하면 엣지가 `edgeStyle=none` 으로 바뀌어 waypoint 가 그대로 그려지고,
라벨에 흰 배경이 붙는다. `lp=` 는 라벨을 선을 따라 이동시킨다.

## 아이콘

추측하지 말고 이름을 조회한다 — 잘못된 경로는 `FileNotFoundError` 로 즉시 실패한다.

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/skills/archplot/scripts')
from drawio_build import find_icon; print(find_icon('mediaconvert'))"
```

결과를 그대로 `icon()` 에 넘긴다. 예: `icon("aws/compute/ec2")`,
`icon("gcp/compute/gke")`, `icon("onprem/client/user")`.

### 경계 종류

`d.group(...)` 에 `kind=` 를 넘긴다. 계정 > 리전 > VPC > 서브넷 순으로 중첩한다.

| `kind` | 용도 |
| --- | --- |
| `account` (기본값) | 계정 경계 |
| `cloud` | AWS Cloud 전체 |
| `region` | 리전 |
| `vpc` | VPC |
| `subnet` | 서브넷 |
| `autoscaling` | Auto Scaling 그룹 |
| `onpremise` | 온프레미스 / 사내 데이터센터 |

## 작도 규칙

AWS 레퍼런스 아키텍처 다이어그램 4장을 비교해 도출했다. 에이전트는 그러지 않을 이유가 없는 한 이를
따른다.

| 규칙 | 관측 |
| --- | --- |
| 곡선 없음 — 90도 orthogonal 엣지만 | 4/4 |
| 엣지 라벨은 1~3 단어(데이터 종류, 프로토콜, 동사 하나) | 4/4 |
| **리소스 하나에 노드 하나** — 같은 버킷의 서로 다른 prefix 는 한 노드로 유지 | 규칙 |
| 노드 라벨은 서비스 이름이며 역할은 괄호에 넣는다. 캡션은 아이콘 아래 최대 두 줄 | 4/4 |
| 액터는 한 종류만, 항상 모든 경계 바깥에, 라벨 없는 엣지로 | 3/4 |
| 선 스타일이 둘이어도 범례는 두지 않는다 | 4/4 |
| 흐름 바깥의 리소스(IAM, CloudWatch)는 엣지 없이 여백에 두거나 뺀다 | 3/4 |
| **아이콘이 있는 것만 노드가 된다** | 4/4 |

마지막 규칙이 추상화 수준을 잡아 준다. 프로토콜과 동작은 아이콘이 없으므로 엣지 라벨로 내려가고,
함수명·URL 경로·필드명은 아이콘도 엣지도 받지 못해 그림에서 완전히 빠진다. 유일한 예외는 AZ 별
복제본이다 — `MySQL (Master)` 와 `MySQL (Slave)` 는 실제로 서로 다른 리소스이므로 각각 노드를 갖는다.

### 그림에 넣지 않을 것

| 그리지 말 것 | 대신 그릴 것 |
| --- | --- |
| 스토리지 경로, prefix, 키 패턴, 파일명 | 버킷이나 큐 이름까지만 |
| HTTP 메서드, URL 경로, 쿼리 파라미터, 페이로드 필드명 | `encode options` 같은 1~3 단어. 경로는 본문 산문에 쓴다 |
| 엣지의 순번 | 화살표 방향이 순서를 전달하도록 배치한다 — 레퍼런스 다이어그램 4장 중 엣지에 번호를 매긴 것은 0장이다 |
| IAM 역할 ARN, STS AssumeRole 화살표 | 아무것도 그리지 않는다 |
| 오류 경로, 재시도, 타임아웃, DLQ | 정상 경로 하나 |
| 함수명, 핸들러명, 테이블 컬럼 | 서비스 이름과 역할 |

## 스크립트

| 파일 | 역할 |
| --- | --- |
| `scripts/drawio_build.py` | `.drawio` 를 빌드한다. `Diagram`, `icon()`, `find_icon()`. 자체 점검: `python3 drawio_build.py` |
| `scripts/drawio_route.py` | 엣지 라우팅. `Panel`, `beside()`. 연결점, orthogonal 경로, 차단 여부를 계산한다. 자체 점검: `python3 drawio_route.py` |
| `scripts/drawio_render.py` | headless Chromium 과 `vendor/viewer-static.min.js` 로 `.drawio` 를 PNG 로 변환한다. `--scale` 기본값은 2 |
| `scripts/drawio_crop.py` | 렌더한 PNG 의 일부를 확대해 라벨 관통을 확인한다. 렌더러와 같은 headless Chromium 을 쓴다 — PIL 도 ImageMagick 도 필요 없다 |
| `scripts/confluence_publish.py` | PNG 를 페이지에 첨부하거나 페이지를 생성한다. md5 로 검증한다 |
| `vendor/viewer-static.min.js` | draw.io 뷰어. 데스크톱 앱과 `xvfb` 가 필요 없도록 벤더링했다 |
| `reference/*.png` | 작도 규칙을 도출한 레퍼런스 다이어그램 4장 |

### Confluence 게시

선택 사항이며, 환경변수 `CONFLUENCE_SITE`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` 으로만
설정한다.

```bash
# refresh the attachment on an existing page (the page body is left alone)
python3 scripts/confluence_publish.py out.png --page <page-id>

# create a page under a parent and attach
python3 scripts/confluence_publish.py out.png --parent <id> --space <KEY> --title "Title"
```

> [!IMPORTANT]
> 같은 파일명을 `POST /child/attachment` 로 다시 올려도 새 버전이 생기지 않는다. 이 스크립트는 기존
> 첨부의 id 를 조회해 `/{id}/data` 로 올린다. 별도 도구로 존재하는 이유가 이것이다.

## 문제 해결

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 아이콘에서 `FileNotFoundError` | 아이콘 경로를 추측했다 | `find_icon()` 으로 검색한다 |
| 아이콘 자리에 빈 사각형 | draw.io 도형 이름을 잘못 썼다 | `icon()` 을 쓴다. draw.io 도형은 경계 전용이다 |
| 캡션이 엣지에 가려짐 | 한 노드의 한 변에 엣지가 셋 이상 | `exit` / `entry` 를 다른 변으로 분산한다 |
| 라벨 둘이 뭉개짐 | 같은 두 노드 사이에 엣지가 둘 | 한쪽에 `label_pos` / `label_offset` 을 설정한다 |
| 경계나 캡션이 이미지 가장자리에서 잘림 | 캔버스 여백 부족 | `drawio_render.py` 의 `PAD` 상수를 올린다 |
| 렌더는 되는데 아이콘이 없음 | AWS4 스텐실을 CDN 에서 가져온다 | 네트워크 접근을 확인한다 |
| Confluence 첨부 버전이 올라가지 않음 | 같은 파일명을 `POST /child/attachment` 로 다시 올렸다 | `confluence_publish.py` 를 쓴다 |
| `ValueError: 생성한 XML 이 깨졌다` | 라벨이나 스타일에 XML 속성을 깨는 문자가 들어갔다. `save()` 가 쓰기 전에 파싱해 내보내지 않는다 | 에러가 출력하는 앞뒤 문맥에서 문제 문자를 찾는다. 라벨의 따옴표는 자동으로 처리되므로, 대개 `_cells` 에 원시 XML 을 직접 넣은 경우다 |

## 다이어그램 도구 고르기

| 요청 | 도구 |
| --- | --- |
| 클라우드 공식 아이콘, 계정·리전·VPC 경계 | 이 스킬 |
| 문서 안에 인라인으로 넣을 흐름도·시퀀스도·상태도 | Mermaid 기반 스킬 — Confluence 와 GitHub 가 그대로 렌더한다 |
| 픽셀 단위 통제 | draw.io 앱을 열어 손으로 그린다 |

## 고지

draw.io / diagrams.net, mxGraph, AWS, Google Cloud, Azure, Kubernetes 및 그 밖의 모든 제품명,
로고, 아이콘은 각 소유자의 상표다. 벤더 아이콘 자산은
[`diagrams`](https://github.com/mingrammer/diagrams) 패키지가 번들한 것이며 각 벤더의 조건에 따라
사용된다.

**제휴 관계 없음.** 이 프로젝트는 draw.io Ltd, draw.io AG, JGraph Ltd 와 제휴 관계가 없으며,
이들로부터 보증이나 후원을 받지 않았다. `draw.io` 는 소유자의 등록상표다(EU 등록 #018062448).

**번들된 뷰어.** `vendor/viewer-static.min.js` 는 draw.io 뷰어 v31.3.1 의 수정되지 않은 사본이며
Apache License 2.0 으로 배포된다. 출처:
`https://github.com/jgraph/drawio/blob/v31.3.1/src/main/webapp/js/viewer-static.min.js`,
SHA256 으로 업스트림 태그 파일과 바이트 단위로 동일함을 확인했다.

**생성한 도면의 책임은 사용자에게 있다.** 벤더별 아이콘 조건이 서로 다르고, 업스트림 `diagrams`
패키지는 자신이 번들한 아이콘 아트워크의 라이선스를 게시하지 않는다. 벤더 아이콘이 들어간 도면을
공개하기 전에 각 벤더가 실제로 밝힌 내용을 정리한 [THIRD-PARTY.md](THIRD-PARTY.md) 를 확인한다.

**아이콘은 재배포하지 않는다.** 이 저장소에는 벤더 아이콘 파일이 들어 있지 않으며, 설치된 `diagrams`
패키지에서 실행 시점에 읽는다. 벤더 아이콘을 이 저장소에 커밋하거나 이 저장소를 통해 재배포하지 않는다.

**아이콘을 변형하지 않는다.** 벤더 아이콘의 종횡비나 색을 바꾸지 않는다 — 벤더 상표 가이드라인이
이를 요구한다.

**렌더링은 외부로 요청을 보낸다.** 번들된 뷰어가 `viewer.diagrams.net` 에서 스텐실·도형·스타일을
가져올 수 있다. 오프라인이거나 폐쇄망에서는 일부 draw.io 도형이 빈 상자로 렌더될 수 있다.

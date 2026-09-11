# archplot

[English](README.md) | 简体中文 | [日本語](README.ja.md)

一个用代码绘制架构图的 Claude Code skill。你写一个简短的 Python 生成器，**用显式坐标**声明节点、
边界和连线，运行它生成 `.drawio` 文件，再用 headless Chromium 加内置的 draw.io viewer 渲染出
PNG —— 不需要 draw.io Desktop，不需要 `xvfb`，不需要 `sudo`。

云厂商图标取自 [`diagrams`](https://github.com/mingrammer/diagrams) 包内置的官方图标 PNG，
以 base64 data URI 直接嵌入 `.drawio` 文件，因此单个文件即可自足。draw.io 自带图形只用于边界框
（账号、区域、VPC、子网）。

> [!NOTE]
> 手写坐标是有意为之。自动布局无法消除标签重叠和多余空白，因此这个 skill 放弃布局自动化，换取
> 对画布的完全控制。真正被自动化的是机械性的那部分：连线走线。

## 特性

- **坐标由你决定** —— 78x78 的图标节点落在 20px 网格上，边界框按内容收紧。
- **正交连线路由器** —— 所有节点摆好之后，路由器挑选连接点并计算 90 度路径，再把它固定为
  waypoint。依次尝试直线、L 形、Z 形、绕行；若不存在可行路径，则抛出 `RuntimeError`，而不是
  悄悄画一条斜线。图标、流程格，以及组标签与节点说明文字的**文字框**，都算作障碍物。
- **2,440 个厂商图标**，覆盖 17 个系列（撰写时 `diagrams` 包所内置的数量） —— `aws`、`gcp`、`azure`、`k8s`、`onprem`、`saas`、
  `generic`、`programming`、`elastic`、`firebase`、`alibabacloud`、`oci`、`ibm`、
  `digitalocean`、`openstack`、`outscale`、`gis`。
- **只要有 Chromium 就能渲染** —— draw.io viewer 已随仓库内置，渲染不需要 GUI，也不需要桌面
  应用。之所以这样实现，是因为 draw.io Desktop CLI 的 export 模式在 WSL 下会卡住。
- **面向 agent 的作图规则** —— `SKILL.md` 中的规则集来自对四张 AWS 参考架构图的比对，让 agent
  按规则作图而不是临场发挥。
- **可选的 Confluence 发布** —— 把渲染出的 PNG 附加到页面，并用 md5 校验。

## 快速开始

### 环境要求

| 要求 | 说明 |
| --- | --- |
| Python 3 | 仅用标准库，无额外运行时依赖 |
| `pip install diagrams` | 提供生成器读取的厂商图标 PNG |
| Chromium | 自动探测 `~/.cache/ms-playwright` 或 `~/.cache/puppeteer`，否则回退到系统的 `chromium` / `chromium-browser` / `google-chrome` |
| 发布到 Confluence（可选） | 需要环境变量 `CONFLUENCE_SITE`、`CONFLUENCE_EMAIL`、`CONFLUENCE_API_TOKEN` |

### 安装

```bash
npx skills add yujung7768903/archplot
```

### 自检

两个脚本都自带自检：

```bash
python3 scripts/drawio_build.py    # demo OK
python3 scripts/drawio_route.py    # drawio_route: ok
```

## 工作方式

生成器 `.py` 是唯一的正本。`.drawio` 和 PNG 都是构建产物，从不手工编辑 —— 看起来不对时，改坐标
并从第 2 步重跑。

| 步骤 | 命令 | 判断依据 |
| --- | --- | --- |
| 1. 编写生成器 | 在 `<name>.py` 中带坐标声明节点、边界与连线 | — |
| 2. 生成 `.drawio` | `python3 <name>.py` | 打印边界数与单元格数 |
| 3. 渲染 PNG | `python3 ~/.claude/skills/archplot/scripts/drawio_render.py <name>.drawio` | 打印画布尺寸 |
| 4. 亲眼看 PNG | 打开图片 | 重叠、裁切、连线打结不会体现在退出码里 |
| 4-1. 放大查看 | `python3 ~/.claude/skills/archplot/scripts/drawio_crop.py <name>.png <x> <y> <w> <h> --zoom 2` | 只看整张不够 —— 缩小之后 1.2px 的线看起来像笔画的一部分，穿过标签的线根本看不出来。把每个组框的左上角（标签所在处）和长说明文字周围逐处放大 |
| 5. 发布（可选） | `python3 ~/.claude/skills/archplot/scripts/confluence_publish.py <name>.png --page <id>` | 打印 md5 一致 |

## 编写生成器

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

这个 skill 内建的布局约定：

- 图标节点为 78x78；坐标对齐到 20px 网格。
- 同一行的 `y` 对齐，列间距保持均匀。
- 只定一条主流向（左→右 或 上→下），回流的线用虚线区分性质。
- 边界框按内容收紧 —— 留下的空白会让图看起来没画完。
- 框内内边距至少 20px，带标签的那一边 40px。
- 同一个节点的同一侧不要接三条以上的线；说明文字在图标下方，会被压住。
- 说明文字在图标下方居中绘制且没有宽度上限，因此**说明文字比图标（78px）更宽的节点，不要使用
  下边的连接点** —— 那条线会竖着穿过文字。
- 改为统一流向：向下的流从出发节点的**侧边**出去，进入目标的**上边**；向上的流从**上边**出去，
  进入目标的**侧边**。需要接收向上连线的节点放在该行的末端，把侧边空出来。
- 间距基准：说明文字为一行时，行间距 160px、列间距 200px 起步。混有三到五行说明文字时，
  需要行间距 220px、列间距 240~300px。
- `exit` 与 `entry` 不是可选项。不给的话，draw.io 会随意贴线，正好压在说明文字上。

## 连线走线

当图中连线超过十条左右，或混入了判断菱形，就不要再手写 `exit` / `entry` / `waypoints`，改用
`Panel`。走线在 `save()` 时计算。

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

| 规则 | 原因 |
| --- | --- |
| 图像图形只用 12 个连接点 —— 每边三个，绝不用四角 | 从角上出去的线看起来像从图标上脱开了 |
| 菱形只用 4 个顶点和 4 个斜边中点，后者写成 `(x, y, "h"\|"v")` 以确定出线方向 | 像 `(1, 0.75)` 这种外接矩形上的点在菱形轮廓之外，draw.io 会把它投影到斜边上，于是第一段变成斜线 |
| 边界组以及其他普通图形只用 4 个边中点，组本身也可以作为连线端点 | 用于整个子网发出的连线 |
| 依次直线 → L → Z → 绕行；两端点共享 x 或 y 时走直线 | 拐弯不是信息 |
| 第一段必须朝所在边的朝向出去 —— 从侧边出去要求目标在其侧方，从上边或下边出去要求目标在其上方或下方。进入端同理 | 否则第一段会往节点内部折回。违反此条会抛 `RuntimeError`，而消息并不区分"被障碍挡住"与"违反方向规则"—— 请先怀疑这一条 |
| 穿过组标签（框的左上角）或节点说明文字（图标下方）的路径会被大幅扣分；确实无路可避时保留该路径并向 stderr 发出警告 | 否则最短路径会径直穿过文字。出现警告时，移动节点或框把那一列空出来 —— 缩小后的 PNG 几乎看不出线穿过文字 |
| 菱形旁边的图标用 `beside(p, cid)` 对齐垂直中心 | 偏 10px 就会出现 4.5px 的碎折 |
| 入线点不与任何东西重合；与出线冲突时用斜边中点钉住（`ep=(0.75, 0.25, "h")`） | 出线一旦失去顶点就会变成斜线 |
| 同两个节点之间的请求/响应两条线用 `sp=` / `ep=` 固定车道 | 单靠打分决定不了哪条线走在上面 |
| `off=` 移动 Z 形的中间线位置 | 路由器不把组边界当障碍，因此无法自行避开穿过框内的路径 |
| 折线路径的直线段不得短于 `MIN_SEG`（24px），否则向 stderr 发出警告 | 过短的段看起来像碎折；把两个节点的间距拉开 |
| 找不到可行路径就抛 `RuntimeError` | 这是要你改布局的信号，而不是悄悄画斜线 |

`import drawio_route` 会把连线切到 `edgeStyle=none`，使 waypoint 被如实绘制，并给标签加白色底。
`lp=` 用于沿线移动标签位置。

## 图标

不要猜名字，查一下 —— 路径写错会立刻以 `FileNotFoundError` 失败。

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/skills/archplot/scripts')
from drawio_build import find_icon; print(find_icon('mediaconvert'))"
```

把结果直接传给 `icon()`，例如 `icon("aws/compute/ec2")`、`icon("gcp/compute/gke")`、
`icon("onprem/client/user")`。

### 边界种类

传给 `d.group(...)` 的 `kind=`。嵌套顺序为 账号 > 区域 > VPC > 子网。

| `kind` | 用途 |
| --- | --- |
| `account`（默认） | 账号边界 |
| `cloud` | 整个 AWS Cloud |
| `region` | 区域 |
| `vpc` | VPC |
| `subnet` | 子网 |
| `autoscaling` | Auto Scaling 组 |
| `onpremise` | 本地机房 / 企业数据中心 |

## 作图规则

来自对四张 AWS 参考架构图的比对。没有相反理由时，agent 就照此执行。

| 规则 | 观察 |
| --- | --- |
| 禁用曲线 —— 只用 90 度正交折线 | 4/4 |
| 连线标签 1~3 个词（数据种类、协议或一个动词） | 4/4 |
| **一个资源一个节点** —— 同一个存储桶内 prefix 不同仍算一个节点 | 规则 |
| 节点标签为服务名，括号内写角色；说明文字在图标下最多两行 | 4/4 |
| 只用一种参与者，永远放在所有边界之外，且连线不带标签 | 3/4 |
| 不做图例，即使有两种线型 | 4/4 |
| 与流程无关的资源（IAM、CloudWatch）无连线地放在空白处，或直接去掉 | 3/4 |
| **只有拥有图标的东西才成为节点** | 4/4 |

最后一条才是守住抽象层次的机制。协议和动作没有图标，于是被挤到连线标签上；函数名、URL 路径、
字段名既得不到图标也得不到连线，直接从图中脱落。唯一的例外是各可用区的副本 ——
`MySQL (Master)` 与 `MySQL (Slave)` 确实是不同资源，各自成为节点。

### 不要画进图里的东西

| 不要画 | 改为 |
| --- | --- |
| 存储路径、prefix、键模式、文件名 | 只到存储桶名或队列名 |
| HTTP 方法、URL 路径、查询参数、载荷字段名 | 像 `encode options` 这样的 1~3 个词；路径写进正文 |
| 连线上的序号 | 用箭头方向表达顺序 —— 四张参考图中给连线编号的有 0 张 |
| IAM 角色 ARN、STS AssumeRole 箭头 | 完全不画 |
| 错误路径、重试、超时、DLQ | 只画一条正常路径 |
| 函数名、handler 名、表字段 | 服务名加角色 |

## 脚本

| 文件 | 作用 |
| --- | --- |
| `scripts/drawio_build.py` | 生成 `.drawio`。`Diagram`、`icon()`、`find_icon()`。自检：`python3 drawio_build.py` |
| `scripts/drawio_route.py` | 连线走线。`Panel`、`beside()`。计算连接点、正交路径与遮挡判定。自检：`python3 drawio_route.py` |
| `scripts/drawio_render.py` | 用 headless Chromium 与 `vendor/viewer-static.min.js` 把 `.drawio` 转成 PNG。`--scale` 默认为 2 |
| `scripts/drawio_crop.py` | 放大渲染后 PNG 的局部，用于检查标签被穿过的情况。使用与渲染器相同的 headless Chromium —— 不需要 PIL，也不需要 ImageMagick |
| `scripts/confluence_publish.py` | 把 PNG 附加到页面，或新建页面；用 md5 校验 |
| `vendor/viewer-static.min.js` | 随仓库内置的 draw.io viewer，因此不需要桌面应用，也不需要 `xvfb` |
| `reference/*.png` | 作图规则所依据的四张参考图 |

### 发布到 Confluence

可选，且完全通过环境变量配置 —— `CONFLUENCE_SITE`、`CONFLUENCE_EMAIL`、
`CONFLUENCE_API_TOKEN`。

```bash
# refresh the attachment on an existing page (the page body is left alone)
python3 scripts/confluence_publish.py out.png --page <page-id>

# create a page under a parent and attach
python3 scripts/confluence_publish.py out.png --parent <id> --space <KEY> --title "Title"
```

> [!IMPORTANT]
> 用同一个文件名再次 `POST /child/attachment` 不会产生新版本。这个脚本会先查出既有附件 id，
> 改为向 `/{id}/data` 提交 —— 这也是它单独存在的原因。

## 疑难排查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 图标报 `FileNotFoundError` | 图标路径是猜的 | 用 `find_icon()` 检索 |
| 图标位置是个空矩形 | draw.io 自带图形名写错了 | 改用 `icon()`；draw.io 图形只用于边界 |
| 说明文字被线压住 | 一个节点的同一侧接了三条以上的线 | 把 `exit` / `entry` 分散到其他边 |
| 两个标签糊在一起 | 同两个节点之间有两条线 | 给其中一条设 `label_pos` / `label_offset` |
| 边界或说明文字在图片边缘被切掉 | 画布留白不足 | 调大 `drawio_render.py` 里的 `PAD` 常量 |
| 渲染成功但图标不出现 | AWS4 模板从 CDN 获取 | 检查网络连通性 |
| Confluence 附件版本不递增 | 同一文件名重复 `POST /child/attachment` | 使用 `confluence_publish.py` |

## 如何选择作图工具

| 需求 | 工具 |
| --- | --- |
| 云厂商官方图标；账号、区域、VPC 边界 | 本 skill |
| 嵌在文档正文里的流程图、时序图、状态图 | 基于 Mermaid 的 skill —— Confluence 与 GitHub 可直接渲染 |
| 需要像素级控制 | 直接打开 draw.io 应用手绘 |

## 声明

draw.io / diagrams.net、mxGraph、AWS、Google Cloud、Azure、Kubernetes 以及其他所有产品名称、
标志与图标，均为各自所有者的商标。厂商图标资源由
[`diagrams`](https://github.com/mingrammer/diagrams) 包内置，并按各厂商的条款使用。

**无关联声明。** 本项目与 draw.io Ltd、draw.io AG、JGraph Ltd 均无关联，也未获得任何背书或
赞助。`draw.io` 是其所有者的注册商标（欧盟注册号 #018062448）。

**内置的 viewer。** `vendor/viewer-static.min.js` 是 draw.io viewer v31.3.1 的未经修改
（unmodified）副本，依 Apache License 2.0 授权。来源：
`https://github.com/jgraph/drawio/blob/v31.3.1/src/main/webapp/js/viewer-static.min.js`，
已用 SHA256 校验与上游 tag 文件逐字节一致。

**不再分发图标。** 本仓库不包含任何厂商图标文件；图标在运行时从已安装的 `diagrams` 包读取。
请不要把厂商图标提交到本仓库，也不要从本仓库再分发它们。

**不要改动图标。** 请不要更改厂商图标的宽高比或颜色 —— 这是厂商商标准则的要求。

**渲染会发出外部请求。** 内置的 viewer 可能会从 `viewer.diagrams.net` 获取模板、图形与样式。
在离线或封闭网络中，部分 draw.io 自带图形可能渲染为空白框。

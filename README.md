# archplot

English | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

A Claude Code skill for drawing architecture diagrams as code. You write a small Python
generator that declares nodes, boundaries and edges **at explicit coordinates**, run it to
produce a `.drawio` file, and render a PNG with headless Chromium and a bundled draw.io
viewer — no draw.io Desktop, no `xvfb`, no `sudo`.

Cloud vendor icons come from the official icon PNGs bundled by the
[`diagrams`](https://github.com/mingrammer/diagrams) package and are embedded directly into
the `.drawio` file as base64 data URIs, so a single file is self-contained. draw.io's own
shapes are used only for boundary boxes (account, region, VPC, subnet).

> [!NOTE]
> Coordinates are specified by hand on purpose. Automatic layout cannot eliminate label
> overlap and dead whitespace, so the skill trades layout automation for full control of
> the canvas. What *is* automated is the part that is mechanical: edge routing.

## Features

- **Coordinates you control** — 78x78 icon nodes on a 20px grid, boundary boxes sized to
  their contents.
- **Orthogonal edge router** — after every node is placed, the router picks connection
  points and computes a 90-degree path, then pins it as waypoints. It tries straight, then
  L, then Z, then a detour; if no valid path exists it raises `RuntimeError` instead of
  silently drawing a diagonal. Icons, flow steps and the text boxes of group labels and
  node captions all count as obstacles.
- **2,440 vendor icons** across 17 families (as bundled by `diagrams` at the time of
  writing) — `aws`, `gcp`, `azure`, `k8s`, `onprem`,
  `saas`, `generic`, `programming`, `elastic`, `firebase`, `alibabacloud`, `oci`, `ibm`,
  `digitalocean`, `openstack`, `outscale`, `gis`.
- **Renders anywhere Chromium runs** — the draw.io viewer is vendored, so rendering needs
  no GUI and no desktop app. It was written this way because the draw.io Desktop CLI's
  export mode hangs under WSL.
- **Drawing rules for the agent** — `SKILL.md` carries a rule set derived by comparing four
  AWS reference architecture diagrams, so the agent draws consistently instead of
  improvising.
- **Optional Confluence publishing** — attach the rendered PNG to a page and verify by md5.

## Getting started

### Requirements

| Requirement | Notes |
| --- | --- |
| Python 3 | Standard library only; no extra runtime dependency |
| `pip install diagrams` | Supplies the vendor icon PNGs the generator reads |
| Chromium | Auto-detected from `~/.cache/ms-playwright` or `~/.cache/puppeteer`, else system `chromium` / `chromium-browser` / `google-chrome` |
| Confluence publishing (optional) | Needs the environment variables `CONFLUENCE_SITE`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` |

### Install

```bash
npx skills add yujung7768903/archplot
```

### Verify

Both scripts ship a self-check:

```bash
python3 scripts/drawio_build.py    # demo OK
python3 scripts/drawio_route.py    # drawio_route: ok
```

## How it works

The generator `.py` is the single source of truth. The `.drawio` and the PNG are build
outputs and are never hand-edited — when something looks wrong, you fix the coordinates and
re-run from step 2.

| Step | Command | What confirms it |
| --- | --- | --- |
| 1. Write the generator | Declare nodes, boundaries and edges with coordinates in `<name>.py` | — |
| 2. Build the `.drawio` | `python3 <name>.py` | Prints boundary and cell counts |
| 3. Render the PNG | `python3 ~/.claude/skills/archplot/scripts/drawio_render.py <name>.drawio` | Prints the canvas size |
| 4. Look at the PNG | Open the image | Overlap, clipping and crossed edges do not show up in an exit code |
| 4-1. Zoom in | `python3 ~/.claude/skills/archplot/scripts/drawio_crop.py <name>.png <x> <y> <w> <h> --zoom 2` | One full-size view is not enough — scaled down, a 1.2px line looks like part of a letter stroke and a line running through a label stays invisible. Zoom the top-left of each group box, where the label sits, and the area around long captions, one at a time |
| 5. Publish (optional) | `python3 ~/.claude/skills/archplot/scripts/confluence_publish.py <name>.png --page <id>` | Prints an md5 match |

## Writing a generator

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

Layout guidance built into the skill:

- Icon nodes are 78x78; snap coordinates to a 20px grid.
- Align `y` within a row and keep column spacing uniform.
- Pick one main axis of flow (left-to-right or top-to-bottom) and make return paths dashed.
- Shrink boundary boxes to fit their contents — leftover space reads as unfinished.
- Keep at least 20px of padding inside a box, 40px on the labelled edge.
- Never attach three or more edges to the same side of a node; captions sit under the icon
  and get covered.
- A caption is drawn centred under the icon with no width limit, so **a node whose caption
  is wider than the icon (78px) must not use its bottom-side connection points** — that
  line runs vertically through the lettering.
- Keep the flow consistent instead: a downward flow leaves by a **side** and enters the
  target's **top**; an upward flow leaves by the **top** and enters the target's **side**.
  Put a node that has to receive an upward line at the end of its row so a side stays free.
- Spacing: with one-line captions, start at 160px between rows and 200px between columns.
  Where captions of three to five lines are mixed in, 220px rows and 240-300px columns.
- `exit` and `entry` are not optional. Without them draw.io attaches the line wherever it
  likes and it lands on a caption.

## Edge routing

Once a diagram has more than about ten edges, or mixes in decision diamonds, stop setting
`exit` / `entry` / `waypoints` by hand and use `Panel` instead. Routing is computed at
`save()` time.

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

| Rule | Why |
| --- | --- |
| Image shapes use 12 connection points — three per side, never the corners | An edge leaving a corner looks detached from the icon |
| Diamonds use only the 4 vertices and the 4 hypotenuse midpoints, the latter written `(x, y, "h"\|"v")` to fix the exit direction | A bounding-box point such as `(1, 0.75)` lies outside the rhombus outline, so draw.io projects it onto the hypotenuse and the first segment turns diagonal |
| Boundary groups and other plain shapes use the 4 side midpoints, and a group can itself be an edge endpoint | For an edge sent by a whole subnet |
| Straight, then L, then Z, then detour — straight whenever both points share an x or a y | A bend is not information |
| The first segment must leave in the direction its side faces — a side exit needs the target beside it, a top or bottom exit needs the target above or below it. The same holds for the entry | Otherwise the first segment cuts back into the node. Breaking this raises `RuntimeError`, and the message does not distinguish "blocked by an obstacle" from "direction rule broken" — suspect this rule first |
| A path crossing a group label (top-left of the box) or a node caption (under the icon) is heavily penalised; where no alternative exists the path is kept and a warning goes to stderr | Otherwise the shortest path runs straight through the lettering. When the warning appears, move nodes or boxes to clear that column — a scaled-down PNG barely shows a line crossing text |
| Align an icon next to a diamond with `beside(p, cid)` | A 10px offset produces a 4.5px stub bend |
| An incoming point never overlaps anything else; pin it to a hypotenuse midpoint (`ep=(0.75, 0.25, "h")`) if it collides with an outgoing edge | An outgoing edge that loses its vertex turns diagonal |
| Request/response pairs between the same two nodes take fixed lanes via `sp=` / `ep=` | Scoring alone does not decide which line runs above |
| `off=` moves the middle line of a Z | The router does not treat group boundaries as obstacles, so it cannot avoid a path that sweeps through a box on its own |
| Straight segments in a bent path must be at least `MIN_SEG` (24px), otherwise a warning goes to stderr | Short segments read as stub bends; widen the gap between the two nodes |
| No valid path raises `RuntimeError` | A signal to fix the layout, not to draw a quiet diagonal |

Importing `drawio_route` switches edges to `edgeStyle=none` so waypoints are drawn
literally, and gives labels a white background. `lp=` shifts a label along its line.

## Icons

Look up a name rather than guessing — a wrong path fails fast with `FileNotFoundError`.

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/skills/archplot/scripts')
from drawio_build import find_icon; print(find_icon('mediaconvert'))"
```

Pass the result straight to `icon()`, e.g. `icon("aws/compute/ec2")`,
`icon("gcp/compute/gke")`, `icon("onprem/client/user")`.

### Boundary kinds

Pass `kind=` to `d.group(...)`. Nest them account > region > VPC > subnet.

| `kind` | Use |
| --- | --- |
| `account` (default) | Account boundary |
| `cloud` | The whole AWS Cloud |
| `region` | Region |
| `vpc` | VPC |
| `subnet` | Subnet |
| `autoscaling` | Auto Scaling group |
| `onpremise` | On-premises / corporate data center |

## Drawing rules

Derived by comparing four AWS reference architecture diagrams. The agent follows them
unless there is a reason not to.

| Rule | Observed |
| --- | --- |
| No curves — 90-degree orthogonal edges only | 4/4 |
| Edge labels are 1-3 words (a data kind, a protocol, one verb) | 4/4 |
| **One resource, one node** — different prefixes in the same bucket stay one node | rule |
| Node label is the service name, with the role in parentheses; captions run at most two lines under the icon | 4/4 |
| One kind of actor only, always outside every boundary, with unlabelled edges | 3/4 |
| No legend, even with two line styles | 4/4 |
| Resources outside the flow (IAM, CloudWatch) go in the margin without edges, or are dropped | 3/4 |
| **Only things that have an icon become nodes** | 4/4 |

That last rule is what holds the level of abstraction. Protocols and actions have no icon,
so they are pushed down to edge labels; function names, URL paths and field names get
neither an icon nor an edge and fall out of the picture entirely. The one exception is
per-AZ replicas — `MySQL (Master)` and `MySQL (Slave)` are genuinely different resources
and get their own nodes.

### Keep out of the picture

| Don't draw | Draw instead |
| --- | --- |
| Storage paths, prefixes, key patterns, filenames | The bucket or queue name and no further |
| HTTP methods, URL paths, query parameters, payload field names | 1-3 words such as `encode options`; paths belong in prose |
| Sequence numbers on edges | Arrange so arrow direction carries the order — 0 of the 4 reference diagrams number their edges |
| IAM role ARNs, STS AssumeRole arrows | Nothing at all |
| Error paths, retries, timeouts, DLQs | The one happy path |
| Function names, handler names, table columns | Service name plus role |

## Scripts

| File | Role |
| --- | --- |
| `scripts/drawio_build.py` | Builds the `.drawio`. `Diagram`, `icon()`, `find_icon()`. Self-check: `python3 drawio_build.py` |
| `scripts/drawio_route.py` | Edge routing. `Panel`, `beside()`. Computes connection points, orthogonal paths and blocking. Self-check: `python3 drawio_route.py` |
| `scripts/drawio_render.py` | `.drawio` to PNG via headless Chromium and `vendor/viewer-static.min.js`. `--scale` defaults to 2 |
| `scripts/drawio_crop.py` | Zooms into part of a rendered PNG, for inspecting label crossings. Uses the same headless Chromium as the renderer — no PIL, no ImageMagick |
| `scripts/confluence_publish.py` | Attaches the PNG to a page, or creates the page; verifies by md5 |
| `vendor/viewer-static.min.js` | The draw.io viewer, vendored so no desktop app and no `xvfb` is needed |
| `reference/*.png` | The four reference diagrams the drawing rules were derived from |

### Publishing to Confluence

Optional, and configured entirely through environment variables — `CONFLUENCE_SITE`,
`CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN`.

```bash
# refresh the attachment on an existing page (the page body is left alone)
python3 scripts/confluence_publish.py out.png --page <page-id>

# create a page under a parent and attach
python3 scripts/confluence_publish.py out.png --parent <id> --space <KEY> --title "Title"
```

> [!IMPORTANT]
> Re-posting the same filename to `POST /child/attachment` does not create a new version.
> The script looks up the existing attachment id and posts to `/{id}/data` instead, which
> is why it exists as a separate tool.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` on an icon | The icon path was guessed | Search with `find_icon()` |
| An empty rectangle where the icon should be | A draw.io shape name was used incorrectly | Use `icon()`; draw.io shapes are for boundaries only |
| A caption hidden behind an edge | Three or more edges on one side of a node | Spread `exit` / `entry` across other sides |
| Two labels smudged together | Two edges running between the same pair of nodes | Set `label_pos` / `label_offset` on one of them |
| Boundary or caption clipped at the image edge | Not enough canvas padding | Raise the `PAD` constant in `drawio_render.py` |
| Renders, but the icons are missing | AWS4 stencils are fetched from a CDN | Check network access |
| The Confluence attachment version does not increase | Same filename re-posted to `POST /child/attachment` | Use `confluence_publish.py` |

## Choosing a diagram tool

| Request | Tool |
| --- | --- |
| Official cloud icons; account, region and VPC boundaries | this skill |
| A flow, sequence or state diagram inline in a document | a Mermaid-based skill — Confluence and GitHub render it as-is |
| Pixel-level control | open the draw.io app and draw it by hand |

## Notices

draw.io / diagrams.net, mxGraph, AWS, Google Cloud, Azure, Kubernetes and all other product
names, logos and icons are trademarks of their respective owners. Vendor icon assets are
bundled by the [`diagrams`](https://github.com/mingrammer/diagrams) package and are used
under their respective vendor terms.

**Not affiliated.** This project is not affiliated with, endorsed by, or sponsored by
draw.io Ltd, draw.io AG, or JGraph Ltd. `draw.io` is a registered trademark of its owner
(EU registration #018062448).

**Bundled viewer.** `vendor/viewer-static.min.js` is an unmodified copy of the draw.io
viewer v31.3.1, licensed under the Apache License 2.0. Source:
`https://github.com/jgraph/drawio/blob/v31.3.1/src/main/webapp/js/viewer-static.min.js`,
verified byte-identical to the upstream tagged file by SHA256.

**Your diagrams are your responsibility.** Vendor icon terms differ, and the upstream
`diagrams` package does not publish a license for the icon artwork it bundles. Before you
publish a diagram containing vendor icons, check [THIRD-PARTY.md](THIRD-PARTY.md), which
records what each vendor actually states.

**Icons are not redistributed.** This repository contains no vendor icon files; they are
read at runtime from the installed `diagrams` package. Do not commit vendor icons to this
repository or redistribute them from it.

**Do not alter icons.** Do not change the aspect ratio or the colors of a vendor icon —
vendor trademark guidelines require this.

**Rendering makes outbound requests.** The bundled viewer may fetch stencils, shapes and
styles from `viewer.diagrams.net`. Offline or on a closed network, some draw.io shapes can
render as empty boxes.

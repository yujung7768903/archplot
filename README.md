# archplot

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

<p align="center">
  <img src="docs/order.png" alt="Order processing flow" width="49%">
  <img src="docs/gateway.png" alt="Gateway authorization flow" width="49%">
</p>

A Claude Code skill that draws architecture diagrams with official cloud icons from a plain
description. You get a `.drawio` file you can open and edit in draw.io, plus a PNG.

## Features

- **Official icons** — 2,440 icons across 17 families, including AWS, GCP, Azure and Kubernetes
- **Boundary boxes** — nest accounts, regions, VPCs and subnets
- **Clean lines** — edges connect at right angles, avoiding shapes and text
- **No app to install** — renders PNGs without the draw.io desktop app

## Install

```bash
npx skills add yujung7768903/archplot
```

Requires Python 3, `pip install diagrams` and Chromium.

## Usage

Describe the setup you want to Claude Code.

> Draw a diagram where the order API puts orders on SQS and a Lambda picks them up and uploads receipts to S3

## Edge rules

Edges connect shapes following these rules.

| Rule | Why |
| --- | --- |
| Bend only horizontally and vertically | Curves and diagonals are hard to follow |
| Never bend when a straight line fits | A bend is not information |
| Never cut through a shape | It becomes unclear where the line ends |
| Never run over text | It hides the name |
| Never leave from an icon corner | The line looks detached from the icon |
| Incoming lines never share a connection point | Overlapping lines read as one |
| If no clean path exists, fix the layout | No forced diagonal lines |

## Drawing rules

Taken from AWS reference architecture diagrams.

- One node per resource
- Only things with an icon become nodes — no function names, URLs or field names
- Edge labels are one to three words
- Users sit outside every boundary box
- Draw the one normal flow — no errors, retries or step numbers

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
repository or redistribute them from it. The one exception is the two example diagrams at the top of
this README (`docs/*.png`), drawn with AWS icons for the architecture-diagram use AWS permits.

**Do not alter icons.** Do not change the aspect ratio or the colors of a vendor icon —
vendor trademark guidelines require this.

**Rendering makes outbound requests.** The bundled viewer may fetch stencils, shapes and
styles from `viewer.diagrams.net`. Offline or on a closed network, some draw.io shapes can
render as empty boxes.

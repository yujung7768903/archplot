# Third-party components

## Included in this repository

### draw.io viewer — `vendor/viewer-static.min.js`

| | |
| --- | --- |
| Version | 31.3.1 |
| Modified | No. Redistributed byte-for-byte; verified by SHA256 against the upstream tag |
| Source | https://github.com/jgraph/drawio/blob/v31.3.1/src/main/webapp/js/viewer-static.min.js |
| License | Apache License 2.0 — copy at `vendor/LICENSE-drawio.txt` |
| Copyright | draw.io Ltd, draw.io AG |

`scripts/drawio_render.py` loads this file from disk and renders a `.drawio` with headless
Chromium. Rendering may fetch stencils, shapes and styles from `viewer.diagrams.net`; on a
closed network some draw.io shapes render as empty boxes.

## Not included — resolved at runtime

### Vendor icons — the `diagrams` package

This repository contains **no vendor icon files**. `scripts/drawio_build.py` reads icon PNGs
from the [`diagrams`](https://github.com/mingrammer/diagrams) package that you install
yourself (`pip install diagrams`), and embeds them into the generated `.drawio` as base64
data URIs. Icons therefore appear only in the diagram output you create, never in this
repository's distribution.

The `diagrams` package itself is MIT licensed. The icon artwork it bundles belongs to the
respective vendors — Amazon Web Services, Microsoft, Google, the Cloud Native Computing
Foundation and others — and is used under each vendor's own terms.

When you create diagrams with this skill:

- Do not change an icon's aspect ratio or its colors.
- Do not commit vendor icon files to this repository, and do not redistribute them from it.

### Chromium

`scripts/drawio_render.py` and `scripts/drawio_crop.py` invoke a Chromium binary that you
already have (Playwright cache, Puppeteer cache, or a system install). No browser binary is
distributed here.

## Trademarks

draw.io and diagrams.net are trademarks of their respective owners; "draw.io" is an EU
registered trademark (#018062448). AWS, Azure, Google Cloud, Kubernetes and all other
product names, logos and icons are trademarks of their respective owners. archplot is not
affiliated with, endorsed by, or sponsored by any of them.

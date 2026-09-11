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

### Vendor icons

This repository contains **no vendor icon files**.

At runtime, this skill reads icon images from the `diagrams` package
(https://github.com/mingrammer/diagrams) installed in the user's own Python
environment, and embeds them as base64 data URIs inside the `.drawio` files it
generates. Icons therefore appear only in diagrams produced by the end user, on
the end user's machine.

The `diagrams` package is licensed under the MIT License
(Copyright (c) 2020 MinJae Kwon). **That MIT license covers the package's code.
It does not grant any rights in the vendor icon artwork bundled with it.** As of
2026-09-11 the upstream project has not published a license notice for the icon
assets; the question has been open as issue #250 since 2020 with no maintainer
response.

Each vendor's own terms apply to its icons:

| Icons | Rights holder | Terms |
|---|---|---|
| AWS Architecture Icons | Amazon Web Services, Inc. | https://aws.amazon.com/architecture/icons/ |
| Azure architecture icons | Microsoft Corporation | https://learn.microsoft.com/en-us/azure/architecture/icons/ |
| Google Cloud product icons | Google LLC | https://cloud.google.com/icons |
| Kubernetes and other CNCF project logos | The Linux Foundation / CNCF | https://www.linuxfoundation.org/legal/trademark-usage |
| Other icon sets bundled by `diagrams` | respective owners | see each vendor |

Summary of what those terms say, as published at the time of writing:

- **AWS** permits customers and partners to use its icons and toolkits to create
  architecture diagrams, including via preexisting icon libraries in third-party
  tools. AWS does not publish a redistribution license for the icon files
  themselves.
- **Microsoft** permits use of the Azure icons "in architectural diagrams,
  training materials, or documentation" and permits copying, distributing and
  displaying them for that permitted use. Icons must not be cropped, flipped,
  rotated, distorted, or otherwise changed in shape, and must not be used to
  represent your own product or service.
- **Google** publishes no usage terms on its icon library page. Use of the Google
  Cloud icons is neither granted nor prohibited there; Google's trademark rules
  apply.
- **CNCF / Linux Foundation** artwork is made available under the Linux
  Foundation trademark usage guidelines, not under a copyright license. Logos
  must not be altered, recolored, combined with other marks, or overlaid, and
  written permission is required to use them in materials promoting your own
  products or services.

This project renders icons unmodified and at a fixed aspect ratio. Do not alter
icon colors or shapes when extending it.

**You are responsible for how you use the diagrams you generate.** Publishing a
diagram that contains vendor icons is your act, not this project's; check the
terms above against your intended use.

### Chromium

`scripts/drawio_render.py` and `scripts/drawio_crop.py` invoke a Chromium binary that you
already have (Playwright cache, Puppeteer cache, or a system install). No browser binary is
distributed here.

## Trademarks

draw.io and diagrams.net are trademarks of their respective owners; "draw.io" is an EU
registered trademark (#018062448). AWS, Azure, Google Cloud, Kubernetes and all other
product names, logos and icons are trademarks of their respective owners. archplot is not
affiliated with, endorsed by, or sponsored by any of them.

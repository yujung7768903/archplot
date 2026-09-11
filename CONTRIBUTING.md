# Contributing

## Rules that are not negotiable

**Never commit vendor icon files.** Icons come from the `diagrams` package at runtime. A PR
that adds icon artwork — AWS, Azure, Google Cloud, Kubernetes or any other vendor — will be
closed. This keeps the distribution free of assets whose redistribution terms we cannot
grant. `.gitignore` already excludes generated `examples/*.drawio` and `examples/*.png`
for the same reason: those embed icons.

**Never commit third-party diagrams or screenshots.** Reference material stays as a link.

## Before you open a PR

Both scripts ship a self-check. Run them:

```bash
python3 scripts/drawio_build.py    # demo OK
python3 scripts/drawio_route.py    # drawio_route: ok
```

Run the examples and look at what they produce:

```bash
python3 examples/basic.py  && python3 scripts/drawio_render.py examples/basic.drawio
python3 examples/routed.py && python3 scripts/drawio_render.py examples/routed.drawio
```

A change to the router needs a case added to its self-check. Rendering must be inspected
visually, not just run — overlap and label penetration do not show up in an exit code, and
a downscaled view hides them. Use `scripts/drawio_crop.py` to zoom in.

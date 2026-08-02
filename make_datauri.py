#!/usr/bin/env python3
"""Generate data URI for wave dots SVG."""

import urllib.parse

with open('wave_dots.svg', 'r') as f:
    svg_content = f.read()

data_uri = 'data:image/svg+xml,' + urllib.parse.quote(svg_content)

with open('wave_dots_datauri.txt', 'w') as f:
    f.write(data_uri)

print(f"Data URI written to wave_dots_datauri.txt ({len(data_uri)} chars)")
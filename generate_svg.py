#!/usr/bin/env python3
"""Generate animated SVG for wave-form dot expansion."""

import math

# Configuration
WIDTH = 1440
HEIGHT = 900
SPACING = 30  # Grid spacing (px) - larger = fewer circles, smaller file
BASE_RADIUS = 1
MAX_RADIUS = 4
WAVE_DURATION = 25  # seconds
WAVE_CYCLES = 1  # one wave at a time

# Diagonal from top-left (0,0) to bottom-right (WIDTH, HEIGHT)
DIAGONAL_LENGTH = math.sqrt(WIDTH**2 + HEIGHT**2)
WAVE_VELOCITY = DIAGONAL_LENGTH / WAVE_DURATION  # px per second

# Diagonal unit vector (TL -> BR)
DX = WIDTH / DIAGONAL_LENGTH
DY = HEIGHT / DIAGONAL_LENGTH

# Generate grid
circles = []
for row in range(0, HEIGHT + SPACING, SPACING):
    for col in range(0, WIDTH + SPACING, SPACING):
        x = col
        y = row
        # Distance along diagonal from top-left
        proj = x * DX + y * DY
        # Delay based on wave travel time
        delay = proj / WAVE_VELOCITY
        circles.append((x, y, delay))

# Sort by delay (wave propagation order)
circles.sort(key=lambda c: c[2])

# Generate SVG
svg_parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">',
    '  <defs>',
    '    <style>',
    '      .dot {',
    f'        fill: currentColor;',
    f'        animation: wave-expand {WAVE_DURATION}s linear infinite;',
    '      }',
    f'      @keyframes wave-expand {{',
    f'        0%, 100% {{ r: {BASE_RADIUS}; }}',
    f'        50% {{ r: {MAX_RADIUS}; }}',
    f'      }}',
    '    </style>',
    '  </defs>',
]

for x, y, delay in circles:
    # Negative delay so wave starts from top-left at t=0
    anim_delay = -delay
    circles_svg = f'    <circle class="dot" cx="{x}" cy="{y}" r="{BASE_RADIUS}" style="animation-delay: {anim_delay:.3f}s;" />'
    svg_parts.append(circles_svg)

svg_parts.append('</svg>')

svg_content = '\n'.join(svg_parts)

# Output as data URI
import urllib.parse
data_uri = 'data:image/svg+xml,' + urllib.parse.quote(svg_content)

print(data_uri)

# Also save raw SVG for inspection
with open('wave_dots.svg', 'w') as f:
    f.write(svg_content)

print(f"\nGenerated {len(circles)} circles")
print(f"SVG size: {len(svg_content)} chars")
print(f"Data URI size: {len(data_uri)} chars")
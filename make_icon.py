# -*- coding: utf-8 -*-
"""Create app.ico (multi-size) for Bounty Radar Pro."""
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "assets", "app.ico")
os.makedirs(os.path.dirname(OUT), exist_ok=True)


def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = max(1, size // 16)
    # rounded square background
    d.rounded_rectangle([m, m, size - m - 1, size - m - 1], radius=size // 5,
                        fill=(16, 185, 129, 255))
    # subtle inner panel
    pad = size // 5
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=size // 8,
                        fill=(4, 47, 46, 180))
    # radar rings
    cx = cy = size // 2
    for i, frac in enumerate([0.38, 0.28, 0.18]):
        r = int(size * frac)
        col = (34, 211, 238, 200) if i % 2 == 0 else (167, 243, 208, 220)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=max(1, size // 48))
    # sweep wedge
    for a in range(-40, 10):
        import math
        ang = math.radians(a)
        x2 = cx + int(size * 0.36 * math.cos(ang))
        y2 = cy + int(size * 0.36 * math.sin(ang))
        d.line([(cx, cy), (x2, y2)], fill=(34, 211, 238, 90), width=1)
    # center + blip
    br = max(2, size // 18)
    d.ellipse([cx - br, cy - br, cx + br, cy + br], fill=(255, 255, 255, 255))
    bx = cx + int(size * 0.18)
    by = cy - int(size * 0.14)
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=(251, 191, 36, 255))
    return img


sizes = [16, 24, 32, 48, 64, 128, 256]
imgs = [draw_icon(s) for s in sizes]
imgs[-1].save(OUT, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
# also save a PNG preview
prev = draw_icon(256)
prev_path = os.path.join(os.path.dirname(__file__), "assets", "app-icon.png")
prev.save(prev_path)
print("saved", OUT, os.path.getsize(OUT))
print("saved", prev_path, os.path.getsize(prev_path))

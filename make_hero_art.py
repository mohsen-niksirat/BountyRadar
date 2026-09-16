# -*- coding: utf-8 -*-
"""Generate landing-page artwork for docs/assets/hero-radar.png"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1536, 864
img = Image.new("RGB", (W, H), (7, 11, 20))
d = ImageDraw.Draw(img, "RGBA")

for cx, cy, r, col in [
    (300, 120, 420, (16, 185, 129, 55)),
    (1200, 180, 380, (34, 211, 238, 45)),
    (760, 720, 400, (167, 139, 250, 35)),
]:
    for i in range(18, 0, -1):
        rr = r * i / 18
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col[:3] + (max(2, col[3] // i),))

for x in range(0, W, 64):
    d.line([(x, 0), (x, H)], fill=(36, 51, 82, 40), width=1)
for y in range(0, H, 64):
    d.line([(0, y), (W, y)], fill=(36, 51, 82, 40), width=1)

cx, cy = W // 2, int(H * 0.52)
base = min(W, H) * 0.38

for i, frac in enumerate([1.0, 0.78, 0.55, 0.32, 0.12]):
    r = base * frac
    col = (34, 211, 238, 70 - i * 8) if i % 2 == 0 else (16, 185, 129, 80 - i * 8)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=3 if i == 0 else 2)

d.line([(cx - base, cy), (cx + base, cy)], fill=(34, 211, 238, 50), width=2)
d.line([(cx, cy - base), (cx, cy + base)], fill=(34, 211, 238, 50), width=2)

sweep = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sweep)
for a in range(0, 50):
    ang = math.radians(a - 50)
    x2 = cx + base * math.cos(ang)
    y2 = cy + base * math.sin(ang)
    sd.polygon(
        [(cx, cy), (x2, y2), (cx + base * math.cos(ang + 0.08), cy + base * math.sin(ang + 0.08))],
        fill=(16, 185, 129, 18),
    )
sweep = sweep.filter(ImageFilter.GaussianBlur(2))
img.paste(sweep, (0, 0), sweep)

blips = [
    (0.62, 0.28, (16, 185, 129)),
    (0.30, 0.58, (34, 211, 238)),
    (0.48, 0.42, (251, 191, 36)),
    (0.70, 0.62, (16, 185, 129)),
    (0.38, 0.35, (34, 211, 238)),
]
for fx, fy, col in blips:
    x = int(W * fx)
    y = int(H * fy)
    for r, a in [(22, 30), (12, 80), (6, 220)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))


def card(x, y, w, h, title, value, sub, accent):
    sh = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([10, 12, w + 10, h + 12], 14, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    img.paste(sh, (x - 10, y - 10), sh)
    d.rounded_rectangle([x, y, x + w, y + h], 14, fill=(17, 26, 46, 230), outline=(36, 51, 82, 220), width=2)
    d.rounded_rectangle([x, y, x + 6, y + h], 3, fill=accent + (220,))
    try:
        font_s = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
        font_b = ImageFont.truetype("C:/Windows/Fonts/seguisb.ttf", 28)
        font_t = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    except Exception:
        font_s = font_b = font_t = ImageFont.load_default()
    d.text((x + 18, y + 14), title, font=font_s, fill=(139, 155, 184, 255))
    d.text((x + 18, y + 34), value, font=font_b, fill=accent + (255,))
    d.text((x + 18, y + 72), sub, font=font_t, fill=(92, 107, 136, 255))


card(60, 120, 240, 110, "PREFLIGHT", "GO 91", "No competing PRs", (134, 239, 172))
card(W - 320, 180, 250, 110, "TOP BOUNTY", "$250", "Fresh - 0 claims", (251, 191, 36))
card(120, H - 220, 250, 110, "SKILL MATCH", "x3", "ui - a11y - react", (34, 211, 238))

d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(16, 185, 129, 255))
d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=(16, 185, 129, 120), width=2)

out = os.path.join(os.path.dirname(__file__), "docs", "assets", "hero-radar.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out, optimize=True)
print("saved", out, img.size, os.path.getsize(out))

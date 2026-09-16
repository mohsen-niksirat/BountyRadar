# -*- coding: utf-8 -*-
"""Generate UI mock screenshots for the GitHub Pages landing."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "docs", "assets")
os.makedirs(OUT, exist_ok=True)

BG = (7, 11, 20)
PANEL = (17, 26, 46)
PANEL2 = (23, 34, 56)
LINE = (36, 51, 82)
INK = (232, 238, 252)
MUTED = (139, 155, 184)
DIM = (92, 107, 136)
ACC = (16, 185, 129)
CYAN = (34, 211, 238)
AMBER = (251, 191, 36)
ROSE = (251, 113, 133)
VIOLET = (167, 139, 250)


def font(size, bold=False):
    paths = [
        r"C:\Windows\Fonts\seguisb.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for p in paths:
        if os.path.isfile(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def rounded(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def shot_dashboard():
    W, H = 1400, 900
    img = Image.new("RGB", (W, H), BG)
    # glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, -150, 500, 350], fill=(16, 185, 129, 40))
    gd.ellipse([900, -100, 1600, 400], fill=(34, 211, 238, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img, "RGBA")

    # top bar
    rounded(d, [40, 36, W - 40, 100], 16, fill=PANEL, outline=LINE, width=2)
    rounded(d, [56, 52, 92, 88], 12, fill=ACC)
    d.text((108, 56), "Bounty Radar Pro", font=font(20, True), fill=INK)
    d.text((108, 78), "v2.2 · EN / فارسی", font=font(12), fill=MUTED)
    # buttons
    rounded(d, [W - 420, 52, W - 300, 84], 10, fill=PANEL2, outline=LINE)
    d.text((W - 390, 62), "Watch", font=font(14), fill=INK)
    rounded(d, [W - 280, 52, W - 180, 84], 10, fill=PANEL2, outline=LINE)
    d.text((W - 258, 62), "Settings", font=font(14), fill=INK)
    rounded(d, [W - 160, 52, W - 56, 84], 10, fill=ACC)
    d.text((W - 138, 62), "Scan", font=font(14, True), fill=(4, 47, 46))

    # sidebar
    rounded(d, [40, 120, 300, H - 40], 16, fill=PANEL, outline=LINE, width=2)
    d.text((60, 140), "PROFILE", font=font(11, True), fill=DIM)
    profiles = [("⌘ Frontend", True), ("⚙ Backend", False), ("✎ Docs", False),
                ("✦ Design", False), ("📱 Mobile", False), ("🛡 Security", False)]
    y = 170
    for name, on in profiles:
        if on:
            rounded(d, [56, y, 284, y + 36], 10, fill=(16, 185, 129, 40), outline=(16, 185, 129, 120))
        d.text((70, y + 10), name, font=font(14, on), fill=(167, 243, 208) if on else MUTED)
        y += 44
    d.text((60, y + 20), "FILTERS", font=font(11, True), fill=DIM)
    y += 48
    for name in ["✓ GO", "Fresh", "Low competition", "Skill match", "★ My claims"]:
        rounded(d, [56, y, 284, y + 32], 10, fill=PANEL2, outline=LINE)
        d.text((70, y + 8), name, font=font(13), fill=MUTED)
        y += 40

    # stats
    stats = [("24", "Bounties", INK), ("$1.8k", "Known $", AMBER), ("9", "Fresh", ACC),
             ("11", "Low comp", CYAN), ("7", "Skill", VIOLET), ("3", "My claims", AMBER)]
    sw = (W - 340 - 20) // 6
    for i, (v, k, c) in enumerate(stats):
        x = 320 + i * sw
        rounded(d, [x, 120, x + sw - 10, 190], 12, fill=PANEL, outline=LINE)
        d.text((x + 14, 136), v, font=font(22, True), fill=c)
        d.text((x + 14, 164), k, font=font(11), fill=DIM)

    # cards
    cards = [
        ("✓ GO 91", ACC, "$250", "Improve booking accessibility", "cal/cal.com#18421", 0.92, "match 3"),
        ("✓ GO 84", ACC, "$120", "Write onboarding docs for API", "twentyhq/twenty#9102", 0.78, "match 2"),
        ("⚠ CAUTION", AMBER, "$80", "Dark-theme icon set", "novuhq/novu#5510", 0.55, "match 4"),
        ("★ Working", CYAN, "$150", "Python SDK retry helper", "triggerdotdev#661", 0.70, "claimed"),
        ("✓ GO 76", ACC, "$100", "Fix mobile budget layout", "maybe-finance#2201", 0.64, "match 2"),
        ("⚠ CAUTION", AMBER, "$60", "Translate settings docs", "refinedev#1204", 0.48, "docs"),
    ]
    cw, ch = 330, 180
    for i, (tag, tc, amt, title, repo, pct, skill) in enumerate(cards):
        col, row = i % 3, i // 3
        x = 320 + col * (cw + 16)
        y = 220 + row * (ch + 16)
        rounded(d, [x, y, x + cw, y + ch], 14, fill=PANEL, outline=LINE, width=2)
        rounded(d, [x + 12, y + 12, x + 90, y + 36], 8, fill=(tc[0], tc[1], tc[2], 40), outline=tc)
        d.text((x + 20, y + 17), tag, font=font(11, True), fill=tc)
        rounded(d, [x + 98, y + 12, x + 160, y + 36], 8, fill=(251, 191, 36, 30), outline=AMBER)
        d.text((x + 110, y + 17), amt, font=font(12, True), fill=AMBER)
        d.text((x + 168, y + 17), skill, font=font(11), fill=CYAN)
        # title wrap
        words = title.split()
        line1, line2 = [], []
        for w in words:
            if len(" ".join(line1 + [w])) < 32:
                line1.append(w)
            else:
                line2.append(w)
        d.text((x + 14, y + 52), " ".join(line1), font=font(14, True), fill=INK)
        if line2:
            d.text((x + 14, y + 74), " ".join(line2), font=font(14, True), fill=INK)
        d.text((x + 14, y + 104), repo, font=font(12), fill=CYAN)
        # score bar
        rounded(d, [x + 14, y + 130, x + cw - 14, y + 140], 5, fill=(12, 20, 36))
        bw = int((cw - 28) * pct)
        rounded(d, [x + 14, y + 130, x + 14 + bw, y + 140], 5, fill=ACC)
        # actions
        for j, label in enumerate(["Open", "Copy", "Why", "★ Claim"]):
            bx = x + 14 + j * 78
            rounded(d, [bx, y + 148, bx + 70, y + 172], 8, fill=PANEL2, outline=LINE)
            d.text((bx + 12, y + 153), label, font=font(11), fill=INK)

    path = os.path.join(OUT, "shot-dashboard.png")
    img.save(path, optimize=True)
    print("saved", path, img.size)


def shot_claim():
    W, H = 1200, 780
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([200, 100, 1000, 700], fill=(16, 185, 129, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img, "RGBA")

    # backdrop dim cards
    rounded(d, [40, 40, W - 40, H - 40], 20, fill=(13, 19, 34), outline=LINE)
    d.text((70, 70), "Scan results", font=font(22, True), fill=MUTED)

    # modal
    mx, my, mw, mh = 180, 100, 840, 580
    sh = Image.new("RGBA", (mw + 40, mh + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 24, mw + 20, mh + 24], 20, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    img.paste(sh, (mx - 20, my - 16), sh)
    rounded(d, [mx, my, mx + mw, my + mh], 18, fill=PANEL, outline=LINE, width=2)
    d.text((mx + 28, my + 24), "Claim workflow", font=font(20, True), fill=INK)
    d.text((mx + 28, my + 52), "cal/cal.com#18421 · Improve booking accessibility…", font=font(13), fill=MUTED)

    d.text((mx + 28, my + 90), "Status", font=font(12), fill=DIM)
    statuses = [("Shortlist", False), ("Working", True), ("Submitted", False), ("Won", False), ("Abandoned", False)]
    sx = mx + 28
    for name, on in statuses:
        w = 100 if name != "Submitted" else 110
        rounded(d, [sx, my + 112, sx + w, my + 144], 10,
                fill=(16, 185, 129, 40) if on else PANEL2,
                outline=(16, 185, 129) if on else LINE)
        d.text((sx + 12, my + 120), name, font=font(13, on), fill=(167, 243, 208) if on else MUTED)
        sx += w + 10

    d.text((mx + 28, my + 170), "Preflight checklist", font=font(12), fill=DIM)
    checks = [
        (True, "Issue is still open on GitHub"),
        (True, "No competing open PRs (or only 1)"),
        (True, "Repo merges external PRs"),
        (True, "Acceptance criteria are clear"),
        (False, "I can build/test locally in reasonable time"),
        (False, "Payout path works for me"),
        (False, "Time budget set (stop if PR not ready by half)"),
    ]
    y = my + 196
    for on, label in checks:
        rounded(d, [mx + 28, y, mx + mw - 28, y + 36], 10, fill=PANEL2, outline=LINE)
        # checkbox
        rounded(d, [mx + 42, y + 10, mx + 60, y + 28], 4, fill=ACC if on else (12, 20, 36), outline=ACC if on else LINE, width=2)
        if on:
            d.line([(mx + 46, y + 19), (mx + 51, y + 24), (mx + 58, y + 14)], fill=(4, 47, 46), width=2)
        d.text((mx + 72, y + 10), label, font=font(13), fill=INK if on else MUTED)
        y += 42

    d.text((mx + 28, y + 8), "Notes", font=font(12), fill=DIM)
    rounded(d, [mx + 28, y + 28, mx + mw - 28, y + 90], 10, fill=PANEL2, outline=LINE)
    d.text((mx + 42, y + 40), "Deadline Friday · branch fix/a11y-booking", font=font(13), fill=MUTED)

    # footer buttons
    by = my + mh - 60
    rounded(d, [mx + 28, by, mx + 120, by + 40], 10, fill=PANEL2, outline=LINE)
    d.text((mx + 48, by + 12), "Remove", font=font(13), fill=ROSE)
    rounded(d, [mx + 136, by, mx + 228, by + 40], 10, fill=PANEL2, outline=LINE)
    d.text((mx + 162, by + 12), "Close", font=font(13), fill=INK)
    rounded(d, [mx + 244, by, mx + 380, by + 40], 10, fill=ACC)
    d.text((mx + 268, by + 12), "Save claim", font=font(13, True), fill=(4, 47, 46))

    path = os.path.join(OUT, "shot-claim.png")
    img.save(path, optimize=True)
    print("saved", path, img.size)


def shot_watch():
    W, H = 1200, 700
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([350, 80, 850, 580], fill=(34, 211, 238, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img.paste(glow, (0, 0), glow)

    # radar
    cx, cy = W // 2, 320
    for i, r in enumerate([220, 170, 120, 70, 28]):
        col = (34, 211, 238, 80) if i % 2 == 0 else (16, 185, 129, 90)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
    d.line([(cx - 230, cy), (cx + 230, cy)], fill=(34, 211, 238, 50), width=1)
    d.line([(cx, cy - 230), (cx, cy + 230)], fill=(34, 211, 238, 50), width=1)
    for fx, fy, col in [(0.65, 0.35, ACC), (0.35, 0.55, CYAN), (0.5, 0.42, AMBER)]:
        x, y = int(W * fx), int(200 + 200 * fy)
        for r, a in [(18, 40), (8, 120), (4, 220)]:
            d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))

    # toast
    rounded(d, [820, 80, 1140, 180], 16, fill=(16, 38, 31), outline=(16, 185, 129, 160), width=2)
    d.text((842, 100), "3 new bounties", font=font(16, True), fill=(167, 243, 208))
    d.text((842, 128), "Top: $250 — cal#18421", font=font(13), fill=MUTED)
    d.text((842, 150), "Preflight GO · 0 claims · fresh", font=font(12), fill=DIM)

    # watch bar
    rounded(d, [60, 560, 1140, 640], 14, fill=PANEL, outline=LINE)
    d.ellipse([90, 590, 106, 606], fill=ACC)
    d.text((120, 585), "Watching · next scan in 04:12", font=font(16, True), fill=INK)
    d.text((120, 612), "First run is a silent baseline · seen.json remembers what you saw", font=font(12), fill=MUTED)
    rounded(d, [900, 585, 1100, 620], 10, fill=ACC)
    d.text((960, 594), "Stop watch", font=font(13, True), fill=(4, 47, 46))

    path = os.path.join(OUT, "shot-watch.png")
    img.save(path, optimize=True)
    print("saved", path, img.size)


if __name__ == "__main__":
    shot_dashboard()
    shot_claim()
    shot_watch()
    print("done")

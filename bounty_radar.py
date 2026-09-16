#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bounty Radar Pro — a local Windows app that finds paid freelance/bounty work.

Works for any freelancer type: frontend, backend, mobile, data/ML, DevOps,
security, docs/writing, design, and "any".

Modes:
  python bounty_radar.py              -> modern web UI (browser)  [default]
  python bounty_radar.py --tk         -> classic Tkinter window
  python bounty_radar.py --scan       -> one-shot console scan
  python bounty_radar.py --watch 15   -> background watch + toast

Data sources (public only, no paid APIs):
  1) Algora organisation bounty pages  -> real $ amounts AND claim counts
  2) GitHub Search API                 -> Algora/Opire labels, bot comments
  3) GitHub REST API (budgeted)        -> stars / activity for top candidates

Every score is explainable — the "why" column shows the exact signals used.
"""

from __future__ import annotations

import csv
import html
import json
import os
import queue
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
SEEN_FILE = os.path.join(APP_DIR, "seen.json")
CACHE_FILE = os.path.join(APP_DIR, "scan_cache.json")
UI_FILE = os.path.join(APP_DIR, "ui", "index.html")
UA = {"User-Agent": "bounty-radar-pro/2.0 (+local desktop app)"}

# ----------------------------------------------------------------------------- profiles
# Freelancer-type presets. Each profile drives GitHub search languages,
# keyword scoring, and which results get a skill-match boost.

PROFILES = {
    "any": {
        "id": "any",
        "label": "Any",
        "icon": "◈",
        "desc": "All stacks, no language filter",
        "languages": [],
        "keywords": [],
        "extra_labels": [],
    },
    "frontend": {
        "id": "frontend",
        "label": "Frontend",
        "icon": "⌘",
        "desc": "React, Vue, CSS, a11y, design systems",
        "languages": ["TypeScript", "JavaScript", "CSS", "HTML", "Vue", "Svelte"],
        "keywords": [
            "frontend", "front-end", "react", "vue", "svelte", "next.js", "nextjs",
            "ui", "ux", "component", "css", "tailwind", "accessibility", "a11y",
            "storybook", "responsive", "dark mode", "theme", "stylesheet", "spa",
        ],
        "extra_labels": ["frontend", "ui", "accessibility", "css"],
    },
    "backend": {
        "id": "backend",
        "label": "Backend",
        "icon": "⚙",
        "desc": "APIs, databases, Python/Go/Rust/Java",
        "languages": ["Python", "Go", "Rust", "Java", "C#", "Ruby", "PHP", "TypeScript"],
        "keywords": [
            "backend", "back-end", "api", "rest", "graphql", "database", "sql",
            "postgres", "mysql", "redis", "server", "endpoint", "middleware",
            "performance", "cli", "sdk", "integration", "webhook",
        ],
        "extra_labels": ["backend", "api", "database"],
    },
    "mobile": {
        "id": "mobile",
        "label": "Mobile",
        "icon": "📱",
        "desc": "iOS, Android, Flutter, React Native",
        "languages": ["Kotlin", "Swift", "Dart", "Java", "TypeScript", "Objective-C"],
        "keywords": [
            "mobile", "ios", "android", "flutter", "react-native", "react native",
            "swift", "kotlin", "app store", "play store", "tablet", "native",
        ],
        "extra_labels": ["mobile", "ios", "android"],
    },
    "data": {
        "id": "data",
        "label": "Data / ML",
        "icon": "📊",
        "desc": "Data engineering, ML, analytics, notebooks",
        "languages": ["Python", "R", "Jupyter Notebook", "SQL", "Scala"],
        "keywords": [
            "data", "ml", "machine learning", "model", "dataset", "pandas",
            "numpy", "etl", "pipeline", "analytics", "visualization", "chart",
            "notebook", "training", "inference", "llm", "embedding",
        ],
        "extra_labels": ["data", "ml", "machine-learning"],
    },
    "devops": {
        "id": "devops",
        "label": "DevOps",
        "icon": "☁",
        "desc": "CI/CD, Docker, Kubernetes, cloud",
        "languages": ["HCL", "Shell", "Dockerfile", "YAML", "Go", "Python"],
        "keywords": [
            "devops", "ci", "cd", "docker", "kubernetes", "k8s", "terraform",
            "helm", "deploy", "pipeline", "github actions", "monitoring",
            "infrastructure", "cloud", "aws", "gcp", "azure", "helm chart",
        ],
        "extra_labels": ["devops", "infrastructure", "ci"],
    },
    "security": {
        "id": "security",
        "label": "Security",
        "icon": "🛡",
        "desc": "AppSec, audits, crypto-adjacent, hardening",
        "languages": ["Python", "Go", "Rust", "C", "C++", "Solidity", "TypeScript"],
        "keywords": [
            "security", "vulnerability", "cve", "audit", "pentest", "xss",
            "csrf", "injection", "auth", "oauth", "jwt", "encryption", "tls",
            "hardening", "threat", "sast", "dast",
        ],
        "extra_labels": ["security"],
    },
    "docs": {
        "id": "docs",
        "label": "Docs / Writing",
        "icon": "✎",
        "desc": "Docs, tutorials, translation, i18n",
        "languages": [],
        "keywords": [
            "docs", "documentation", "readme", "tutorial", "guide", "howto",
            "how-to", "translation", "translate", "i18n", "l10n", "localization",
            "localisation", "copywriting", "blog", "changelog", "example",
            "onboarding", "handbook", "manual", "wiki",
        ],
        "extra_labels": ["documentation", "docs", "good first issue"],
    },
    "design": {
        "id": "design",
        "label": "Design",
        "icon": "✦",
        "desc": "UI/UX, icons, branding, illustrations",
        "languages": [],
        "keywords": [
            "design", "ui", "ux", "figma", "logo", "icon", "illustration",
            "brand", "mockup", "wireframe", "typography", "palette", "visual",
            "style guide", "design system", "graphic", "svg", "icon set",
        ],
        "extra_labels": ["design", "ux", "ui"],
    },
    "fullstack": {
        "id": "fullstack",
        "label": "Full-stack",
        "icon": "⬡",
        "desc": "End-to-end web apps",
        "languages": ["TypeScript", "JavaScript", "Python", "Go", "Ruby"],
        "keywords": [
            "fullstack", "full-stack", "full stack", "web app", "monorepo",
            "feature", "dashboard", "auth", "billing", "admin", "crud",
        ],
        "extra_labels": ["fullstack"],
    },
}

# ----------------------------------------------------------------------------- config

DEFAULT_ORGS = [
    "tscircuit", "drizzle-team", "cal", "triggerdotdev", "highlight",
    "maybe-finance", "twentyhq", "novuhq", "refinedev", "unkeyed",
    "apache", "grafana", "supabase", "posthog", "n8n-io",
]

DENY_OWNERS = {
    "xevrion-v2", "securebananalabs", "bawes-universe", "unsafelabs", "ikalus1988",
    "lb1192176991-lab", "bounty-plaza", "zhangjiayang6835-cyber",
}
DENY_TITLE_RE = re.compile(
    r"(\[bounty\]\[\$0\]|calculate the exact value|universe into omniblocks"
    r"|\[\s*crypto\s*\]|flash loan|replay attack|tx\.origin|price manipulation"
    r"|integer overflow in token|multisigwallet|priceoracle|crosschainbridge)",
    re.I,
)
ABSURD_AMOUNT = 20000.0

DEFAULT_SETTINGS = {
    "token": "",
    "profile": "any",
    "languages": [],
    "min_amount": 10.0,
    "max_claims": 20,
    "max_age_days": 1200,
    "fresh_days": 30,
    "active_only": False,
    "hide_farms": True,
    "orgs": DEFAULT_ORGS,
    "use_github_search": True,
    "use_opire_bot": True,
    "enrich_limit": 20,
    "preflight_limit": 12,
    "auto_discover_orgs": True,
    "watch": False,
    "watch_minutes": 15,
    "cache_minutes": 5,
    "theme": "dark",
    "view": "cards",
}

# Back-compat: older settings.json may still store ts+js languages without a profile.
_LEGACY_LANG = {
    "ts": ["TypeScript"],
    "js": ["JavaScript"],
    "ts+js": ["TypeScript", "JavaScript"],
    "any": [],
}


def load_settings():
    s = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    prof = s.get("profile") or "any"
    if prof not in PROFILES:
        prof = "any"
        s["profile"] = prof
    # Languages come from the profile unless the user overrode them.
    if not s.get("languages"):
        s["languages"] = list(PROFILES[prof]["languages"])
    return s


def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ------------------------------------------------------------------ watch mode support

def key_of(item):
    return f"{item['repo'].lower()}#{item['number']}"


def load_seen():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_seen(seen):
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(seen, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def mark_new(results, log=None):
    """Flag bounties never seen before, persist them, and return how many are new.
    The very first scan ever is a baseline, so a fresh install does not shout about
    every existing bounty it just discovered."""
    seen = load_seen()
    baseline = not seen
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for it in results:
        k = key_of(it)
        it["is_new"] = (not baseline) and (k not in seen)
        if k not in seen:
            seen[k] = now
    save_seen(seen)
    new_count = sum(1 for it in results if it.get("is_new"))
    if log:
        if baseline:
            log("[watch] first run recorded as baseline (no alerts)")
        else:
            log(f"[watch] {new_count} new bounties since last scan")
    return new_count


_TOAST_PS = r"""
$ErrorActionPreference = 'Stop'
[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]
[void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType=WindowsRuntime]
$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$texts = $t.GetElementsByTagName('text')
[void]$texts.Item(0).AppendChild($t.CreateTextNode($env:BR_TITLE))
[void]$texts.Item(1).AppendChild($t.CreateTextNode($env:BR_MSG))
$toast = [Windows.UI.Notifications.ToastNotification]::new($t)
$appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
"""


def notify(title, message, log=None):
    """Windows toast notification. Never raises: a failed notification must not break a scan."""
    if os.name != "nt":
        return False
    env = dict(os.environ, BR_TITLE=str(title)[:120], BR_MSG=str(message)[:250])
    try:
        import subprocess
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
             "-ExecutionPolicy", "Bypass", "-Command", _TOAST_PS],
            env=env, capture_output=True, timeout=30)
        if r.returncode == 0:
            return True
        if log:
            err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
            log("[notify] toast failed: " + (err[-1][:160] if err else "unknown"))
    except Exception as e:
        if log:
            log(f"[notify] {type(e).__name__}: {e}")
    return False


def notify_new_bounties(new_items, log=None):
    """One consolidated notification for everything that appeared since the last scan."""
    if not new_items:
        return False
    best = new_items[0]
    amount = "$?" if best.get("amount") is None else f"${best['amount']:.0f}"
    head = f"{len(new_items)} new bounties"
    body = (f"Top: {amount} — {best.get('repo_short', best['repo'].split('/')[-1])}"
            f"#{best['number']}\n{best['title'][:120]}")
    return notify(head, body, log=log)


# ----------------------------------------------------------------------------- http

_last_request = [0.0]


def http_get(url, token=None, accept="application/json", min_interval=0.0, timeout=25):
    """GET with polite throttling. Returns (text, headers). Raises RuntimeError on failure."""
    wait = min_interval - (time.time() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    headers = dict(UA)
    headers["Accept"] = accept
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            _last_request[0] = time.time()
            return r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        _last_request[0] = time.time()
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        if e.code in (403, 429):
            raise RuntimeError(f"rate limit ({e.code}) — add a GitHub token or wait a few minutes")
        raise RuntimeError(f"HTTP {e.code} {body}")
    except Exception as e:
        _last_request[0] = time.time()
        raise RuntimeError(f"network: {e}")


def html_lines(page):
    page = re.sub(r"(?is)<script.*?</script>", " ", page)
    page = re.sub(r"(?is)<style.*?</style>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", "\n", page)
    page = html.unescape(page)
    return [l.strip() for l in page.split("\n") if l.strip()]


AGE_RE = re.compile(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", re.I)
_UNIT_DAYS = {"second": 0, "minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30, "year": 365}


def age_to_days(text):
    m = AGE_RE.search(text or "")
    if not m:
        return None
    return int(m.group(1)) * _UNIT_DAYS[m.group(2).lower()]


# ----------------------------------------------------------------------------- sources

def scan_algora(orgs, settings, log):
    """Parse https://algora.io/<org>/bounties -> real amounts + claim counts."""
    all_rows = []
    for org in orgs:
        org = org.strip().lstrip("@")
        if not org:
            continue
        url = f"https://algora.io/{urllib.parse.quote(org)}/bounties"
        try:
            page, _ = http_get(url, accept="text/html", min_interval=0.35)
        except RuntimeError as e:
            log(f"[algora] {org}: {e}")
            continue
        rows = _parse_algora_page(page)
        log(f"[algora] {org}: {len(rows)} bounty rows")
        all_rows.extend(rows)
    return aggregate_rows(all_rows)


def aggregate_rows(rows):
    """Merge rows describing the same issue: several people can stack rewards on one
    issue (amounts add up) and the same issue can appear on two org pages."""
    agg = {}
    for r in rows:
        key = (r["repo"].lower(), r["number"])
        cur = agg.get(key)
        if cur is None:
            agg[key] = dict(r)
            continue
        if r.get("amount") is not None:
            cur["amount"] = (cur.get("amount") or 0) + r["amount"]
        if r.get("claims") is not None:
            cur["claims"] = max(cur.get("claims") or 0, r["claims"])
        if cur.get("age_days") is None:
            cur["age_days"] = r.get("age_days")
        if not cur.get("title"):
            cur["title"] = r.get("title", "")
    return agg


def _parse_algora_page(page):
    """Each bounty row in Algora's HTML looks like:
         <div ...>$50</div></div></div></div>
         <a href="https://github.com/OWNER/NAME/issues/123" ...>
           ... NAME#123 ... <p class="line-clamp-2...">TITLE</p>
         </a> ... N months ago ... N claims ...
    """
    rows = []
    chunks = page.split('href="https://github.com/')
    for idx in range(1, len(chunks)):
        piece = chunks[idx]
        url = "https://github.com/" + piece.split('"', 1)[0]
        m = re.match(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", url)
        if not m:
            continue
        owner, name, number = m.group(1), m.group(2), int(m.group(3))
        prev = chunks[idx - 1]
        amounts = re.findall(r"\$\s*([\d,]+(?:\.\d+)?)", prev)
        amount = float(amounts[-1].replace(",", "")) if amounts else None
        tm = re.search(r'line-clamp-2[^>]*>\s*(.*?)</p>', piece, re.S)
        title = html.unescape(re.sub(r"\s+", " ", tm.group(1))).strip() if tm else ""
        after = piece[tm.end():] if tm else piece
        nxt = re.search(r"\$\s*[\d,]+", after)
        window = after[: nxt.start()] if nxt else after[:2500]
        age_m = AGE_RE.search(window)
        cl_m = re.search(r"(\d+)\s+claims?", window, re.I)
        rows.append({
            "source": "algora",
            "platform": "Algora",
            "repo": f"{owner}/{name}",
            "repo_short": name,
            "number": number,
            "title": title or f"{name}#{number}",
            "amount": amount,
            "amount_estimated": False,
            "claims": int(cl_m.group(1)) if cl_m else None,
            "age_days": age_to_days(age_m.group(0)) if age_m else None,
            "age_text": age_m.group(0) if age_m else "",
            "url": url,
        })
    if not rows:
        rows = _parse_algora_text(page)
    return rows


def _parse_algora_text(page):
    """Fallback parser that works on tag-stripped text (no owner info)."""
    L = html_lines(page)
    rows, i = [], 0
    while i < len(L):
        m = re.fullmatch(r"\$([\d,]+(?:\.\d+)?)", L[i])
        if m and i + 2 < len(L):
            rm = re.fullmatch(r"([\w.\-]+)#(\d+)", L[i + 1])
            if rm:
                j = i + 3
                age_days, claims = None, None
                if j < len(L) and AGE_RE.search(L[j]):
                    age_days = age_to_days(L[j])
                    j += 1
                if j < len(L):
                    cm = re.fullmatch(r"(\d+)\s+claims?", L[j])
                    if cm:
                        claims = int(cm.group(1))
                        j += 1
                rows.append({
                    "source": "algora", "platform": "Algora",
                    "repo": rm.group(1), "repo_short": rm.group(1),
                    "number": int(rm.group(2)), "title": L[i + 2],
                    "amount": float(m.group(1).replace(",", "")),
                    "amount_estimated": False, "claims": claims,
                    "age_days": age_days, "age_text": "",
                    "url": f"https://github.com/{rm.group(1)}",
                })
                i = j
                continue
        i += 1
    return rows


def _gh_search(query, token, log, min_interval):
    url = ("https://api.github.com/search/issues?per_page=40&sort=created&order=desc&q="
           + urllib.parse.quote(query))
    try:
        text, _ = http_get(url, token=token,
                           accept="application/vnd.github+json",
                           min_interval=min_interval)
    except RuntimeError as e:
        log(f"[github] «{query}» → {e}")
        return []
    try:
        data = json.loads(text)
    except Exception:
        return []
    items = data.get("items", [])
    total = data.get("total_count", len(items))
    log(f"[github] «{query}» → {total} hits (read {len(items)})")
    out = []
    for it in items:
        rp = it.get("repository_url", "")
        repo_full = rp.split("/repos/")[-1] if "/repos/" in rp else ""
        if "/" not in repo_full:
            continue
        title = it.get("title", "")
        body = (it.get("body") or "")[:400]
        amount = None
        for m in re.finditer(r"\$([\d,]+(?:\.\d+)?)", title + " " + body):
            try:
                v = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            if 1 <= v <= ABSURD_AMOUNT:
                amount = v if amount is None else max(amount, v)
        created = it.get("created_at") or ""
        age_days = None
        try:
            dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - dt).days
        except Exception:
            pass
        labels = [l.get("name", "") for l in it.get("labels", [])]
        out.append({
            "source": "github",
            "platform": "Opire" if any("Reward" in l for l in labels) else "Algora/GitHub",
            "repo": repo_full,
            "repo_short": repo_full.split("/")[-1],
            "number": it.get("number"),
            "title": title,
            "amount": amount,
            "amount_estimated": True,
            "claims": None,
            "age_days": age_days,
            "age_text": (f"{age_days} days ago" if age_days is not None else ""),
            "url": it.get("html_url", ""),
            "labels": labels,
            "comments": it.get("comments", 0),
            "body": body,
        })
    return out


def profile_languages(settings):
    prof_id = settings.get("profile") or "any"
    prof = PROFILES.get(prof_id, PROFILES["any"])
    langs = settings.get("languages")
    if langs:
        return list(langs)
    return list(prof.get("languages") or [])


def build_github_queries(settings):
    """Language + label queries for the active freelancer profile.
    Includes date-partitioned queries so we don't silently lose the 1000-result cap.
    """
    langs = profile_languages(settings)
    lang_clause = " ".join(f"language:{l}" for l in langs)
    queries = []
    if settings.get("use_github_search", True):
        queries.append(f'label:"💎 Bounty" is:issue is:open {lang_clause}'.strip())
        queries.append(f'label:"💰 Reward" is:issue is:open {lang_clause}'.strip())
        # Partition the noisy generic label by recency to stay under the 1000-result cap.
        queries.append(f'label:bounty is:issue is:open created:>2025-01-01 {lang_clause}'.strip())
        queries.append(f'label:bounty is:issue is:open created:2024-01-01..2024-12-31 {lang_clause}'.strip())
        # Comment-command signal: the actual funding primitive on Algora/Opire.
        queries.append(f'"/bounty $" in:comments is:issue is:open {lang_clause}'.strip())
        queries.append(f'"/reward" in:comments is:issue is:open commenter:opirebot[bot] {lang_clause}'.strip())
    if settings.get("use_opire_bot", True):
        queries.append(f'commenter:"opirebot[bot]" is:issue is:open {lang_clause}'.strip())
    prof = PROFILES.get(settings.get("profile") or "any", PROFILES["any"])
    for lab in (prof.get("extra_labels") or [])[:2]:
        if settings.get("use_github_search", True):
            queries.append(f'label:"{lab}" bounty is:issue is:open'.strip())
    seen, out = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:8]


ALGORA_ORG_RE = re.compile(r"https?://algora\.io/([A-Za-z0-9_.-]+)/bounties?", re.I)
ALGORA_CMD_RE = re.compile(r"/bounty\s+\$?\s*([\d,]+(?:\.\d+)?)", re.I)
REWARD_CMD_RE = re.compile(r"/reward\s+\$?\s*([\d,]+(?:\.\d+)?)", re.I)


def extract_amounts_from_text(*chunks):
    """Pull plausible bounty amounts from titles, bodies, bot comments."""
    amount = None
    text = " ".join(c or "" for c in chunks)
    # Prefer explicit funding commands over loose $ mentions.
    for rx in (ALGORA_CMD_RE, REWARD_CMD_RE):
        for m in rx.finditer(text):
            try:
                v = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            if 1 <= v <= ABSURD_AMOUNT:
                amount = v if amount is None else max(amount, v)
    if amount is None:
        for m in re.finditer(r"\$([\d,]+(?:\.\d+)?)", text):
            try:
                v = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            if 1 <= v <= ABSURD_AMOUNT:
                amount = v if amount is None else max(amount, v)
    return amount


def discover_algora_orgs(items, log=None, extra_text=""):
    """Harvest Algora org handles from issue bodies / links already in hand."""
    orgs = set()
    for it in items:
        blob = " ".join([
            it.get("url") or "",
            it.get("body") or "",
            it.get("title") or "",
            " ".join(it.get("labels") or []),
        ])
        for m in ALGORA_ORG_RE.finditer(blob + " " + extra_text):
            orgs.add(m.group(1))
    if orgs and log:
        log(f"[discover] algora orgs from GitHub links: {', '.join(sorted(orgs)[:12])}")
    return sorted(orgs)


def scan_github(settings, log):
    token = settings.get("token") or None
    min_interval = 2.1 if token else 6.5
    queries = build_github_queries(settings)
    results = []
    for q in queries:
        results.extend(_gh_search(q, token, log, min_interval))
    # Improve amounts using command regex on the fuller fields.
    for it in results:
        better = extract_amounts_from_text(it.get("title"), it.get("body"), it.get("amount_text"))
        if better is not None:
            if it.get("amount") is None:
                it["amount"] = better
                it["amount_estimated"] = True
            else:
                it["amount"] = max(it["amount"], better)
    return results


def enrich_repos(items, settings, log, limit=15, known=None):
    """Add stars / activity / archived so we can rank repository quality."""
    token = settings.get("token") or None
    known = known if known is not None else {}
    seen, cur = {}, {}
    targets = []
    for it in items:
        repo = it["repo"]
        if repo not in seen:
            seen[repo] = None
            if repo not in known:
                targets.append(repo)
    targets = targets[:max(0, limit)]
    for repo in targets:
        try:
            text, _ = http_get(f"https://api.github.com/repos/{repo}", token=token,
                               accept="application/vnd.github+json", min_interval=0.25)
            cur[repo] = json.loads(text)
            known[repo] = cur[repo]
        except RuntimeError as e:
            log(f"[enrich] {repo}: {e}")
            if "rate limit" in str(e):
                break
    for it in items:
        r = cur.get(it["repo"]) or known.get(it["repo"])
        if not r:
            continue
        it["stars"] = r.get("stargazers_count")
        it["archived"] = r.get("archived")
        it["pushed_days"] = _days_since(r.get("pushed_at"))
        it["repo_created_days"] = _days_since(r.get("created_at"))
        it["open_issues"] = r.get("open_issues_count")
    log(f"[enrich] repo info for {len(cur)} repositories (cache hit {len(known) - len(cur) if known else 0})")
    return items


# ----------------------------------------------------------------------------- preflight quality
# Turns the 9-point checklist into automated signals we can score and show.

PREFLIGHT_CACHE = {}  # (repo.lower(), number) -> preflight dict


def _gh_json(url, token, min_interval=0.35, timeout=20):
    text, _ = http_get(url, token=token, accept="application/vnd.github+json",
                       min_interval=min_interval, timeout=timeout)
    return json.loads(text)


def count_open_prs_for_issue(repo, number, token=None, log=None, min_interval=0.4):
    """How many open PRs already target this issue (competitors)."""
    # Timeline/events are cheaper and more precise than full search when available.
    url = f"https://api.github.com/repos/{repo}/issues/{number}/timeline?per_page=100"
    try:
        data = _gh_json(url, token, min_interval=min_interval)
    except RuntimeError as e:
        # Fallback: search for PRs mentioning the issue number.
        try:
            q = urllib.parse.quote(f"repo:{repo} is:pr is:open {number}")
            data = _gh_json(
                f"https://api.github.com/search/issues?q={q}&per_page=10",
                token, min_interval=max(min_interval, 2.2))
            return int(data.get("total_count") or 0)
        except RuntimeError:
            if log:
                log(f"[preflight] {repo}#{number}: {e}")
            return None
    prs = set()
    for ev in data if isinstance(data, list) else []:
        if not isinstance(ev, dict):
            continue
        # cross-referenced / connected PRs
        src = ev.get("source") or {}
        issue = (src.get("issue") or {}) if isinstance(src, dict) else {}
        if issue.get("pull_request"):
            prs.add(issue.get("html_url") or issue.get("number"))
        # explicit PR URL in event payload
        blob = json.dumps(ev)
        for m in re.finditer(rf"https://github\.com/{re.escape(repo)}/pull/(\d+)", blob):
            prs.add(int(m.group(1)))
    prs.discard(None)
    return len(prs)


def repo_merge_profile(repo, token=None, log=None, min_interval=0.4, known=None):
    """Does this repo actually merge external PRs? Uses recent closed PRs."""
    if known is not None and repo in known.get("merge", {}):
        return known["merge"][repo]
    url = f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page=20&sort=updated&direction=desc"
    try:
        prs = _gh_json(url, token, min_interval=min_interval)
    except RuntimeError as e:
        if log:
            log(f"[preflight] merge-profile {repo}: {e}")
        return None
    if not isinstance(prs, list) or not prs:
        return {"merged_total": 0, "sampled": 0, "external_merged": 0, "ok": None}
    merged = 0
    external = 0
    for pr in prs:
        if not pr.get("merged_at"):
            continue
        merged += 1
        user = ((pr.get("user") or {}).get("login") or "").lower()
        owner = repo.split("/")[0].lower()
        # Outside contributors: not the org/user itself and not obvious bots.
        if user and user != owner and not user.endswith("[bot]"):
            external += 1
    result = {
        "merged_total": merged,
        "sampled": len(prs),
        "external_merged": external,
        "ok": merged >= 3 and external >= 1,
    }
    if known is not None:
        known.setdefault("merge", {})[repo] = result
    return result


def preflight_item(item, settings, log=None, known=None, min_interval=0.5):
    """Compute preflight quality for one bounty. Returns a dict, never raises."""
    repo = item["repo"]
    number = item.get("number")
    token = settings.get("token") or None
    key = (repo.lower(), number)
    if key in PREFLIGHT_CACHE:
        return PREFLIGHT_CACHE[key]

    factors = []
    issues_open = True
    # 1) Is the issue still open? (cheap repo call when we have a token)
    if token and number is not None:
        try:
            meta = _gh_json(f"https://api.github.com/repos/{repo}/issues/{number}",
                            token, min_interval=min_interval)
            state = meta.get("state")
            issues_open = state == "open"
            if not issues_open:
                factors.append("issue closed on GitHub")
            if meta.get("locked"):
                factors.append("issue locked")
            body = (meta.get("body") or "") + " " + (meta.get("title") or "")
            # acceptance-criteria heuristic
            if re.search(r"(acceptance criteria|expected behaviour|expected behavior|how to test|repro steps)", body, re.I):
                factors.append("acceptance criteria present")
            elif len(body) < 80:
                factors.append("thin issue body")
        except RuntimeError as e:
            if log:
                log(f"[preflight] issue {repo}#{number}: {e}")

    open_prs = 0
    if number is not None:
        n = count_open_prs_for_issue(repo, number, token=token, log=log, min_interval=min_interval)
        if n is not None:
            open_prs = n
            if n == 0:
                factors.append("no competing PRs")
            elif n == 1:
                factors.append("1 competing PR")
            else:
                factors.append(f"{n} competing PRs")

    merge = repo_merge_profile(repo, token=token, log=log, min_interval=min_interval, known=known)
    if merge:
        if merge.get("ok") is True:
            factors.append(f"merges external PRs ({merge['external_merged']}/{merge['sampled']})")
        elif merge.get("ok") is False:
            factors.append("rarely merges external PRs")
        else:
            factors.append("merge history unclear")

    # Overall verdict
    stop = (not issues_open) or (open_prs is not None and open_prs >= 3) or (
        merge and merge.get("ok") is False and (open_prs or 0) >= 1)
    caution = (not stop) and (
        (open_prs or 0) >= 1
        or (merge and merge.get("ok") is None)
        or any(f == "thin issue body" for f in factors)
        or (item.get("age_days") or 0) > 180
    )
    if stop:
        verdict = "STOP"
    elif caution:
        verdict = "CAUTION"
    else:
        verdict = "GO"

    # 0–100 quality score used as a ranking factor
    score = 50.0
    if issues_open:
        score += 15
    else:
        score -= 40
    if open_prs == 0:
        score += 15
    elif open_prs == 1:
        score -= 5
    elif (open_prs or 0) >= 2:
        score -= 20
    if merge and merge.get("ok") is True:
        score += 15
    elif merge and merge.get("ok") is False:
        score -= 15
    if any("acceptance criteria" in f for f in factors):
        score += 8
    if any(f == "thin issue body" for f in factors):
        score -= 8
    score = max(0.0, min(100.0, score))

    out = {
        "verdict": verdict,
        "score": round(score, 1),
        "open_prs": open_prs,
        "issue_open": issues_open,
        "factors": factors,
        "merge_ok": (merge or {}).get("ok"),
        "external_merged": (merge or {}).get("external_merged"),
    }
    PREFLIGHT_CACHE[key] = out
    return out


def preflight_top_items(items, settings, log, limit=12, known=None):
    """Run preflight on the top candidates only (API-budget aware)."""
    limit = max(0, int(settings.get("preflight_limit", 12) or 0))
    if limit == 0:
        return items
    done = 0
    for it in items:
        if done >= limit:
            break
        try:
            pf = preflight_item(it, settings, log=log, known=known)
        except Exception as e:
            if log:
                log(f"[preflight] {it.get('repo')}#{it.get('number')}: {e}")
            continue
        it["preflight"] = pf
        done += 1
    if log:
        log(f"[preflight] checked {done} top bounties (GO/CAUTION/STOP)")
    return items


def _days_since(iso):
    if not iso:
        return None
    try:
        dt = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return None


# ----------------------------------------------------------------------------- scoring

def is_denied(item, settings):
    if not settings.get("hide_farms", True):
        return False
    owner = item["repo"].split("/")[0].lower()
    if owner in DENY_OWNERS:
        return True
    if DENY_TITLE_RE.search(item.get("title") or ""):
        return True
    if item.get("amount") and item["amount"] > ABSURD_AMOUNT:
        return True
    if item.get("amount") == 0:
        return True
    return False


def skill_boost(item, profile_id):
    """Return (multiplier, matched_keywords[]) when the bounty matches the profile."""
    prof = PROFILES.get(profile_id or "any", PROFILES["any"])
    keywords = prof.get("keywords") or []
    if not keywords:
        return 1.0, []
    text = ((item.get("title") or "") + " " + " ".join(item.get("labels") or [])).lower()
    hits = [k for k in keywords if k in text]
    if not hits:
        return 1.0, []
    # More keyword hits → higher skill-match boost, capped.
    boost = min(1.45, 1.0 + 0.12 * len(hits))
    return boost, hits[:5]


def score_item(it, settings):
    """Transparent expected-value score. Returns (score, reasons[])."""
    reasons = []
    amount = it.get("amount") or 0.0
    if it.get("amount") is None:
        assumed = 25.0 * (0.8 if it.get("claims") is None else 0.9)
        reasons.append("amount unknown — verify on the platform")
    else:
        assumed = amount
        reasons.append(("${:,.0f}".format(amount)) + (" (estimated from text)" if it.get("amount_estimated") else ""))

    score = assumed
    claims = it.get("claims")
    if claims:
        score = score / (1.0 + claims)
        reasons.append(f"{claims} claim(s)")
    elif claims == 0:
        reasons.append("no claims yet")
    else:
        reasons.append("claims unknown")

    age = it.get("age_days")
    fresh = settings.get("fresh_days", 30)
    if age is not None:
        if age <= 7:
            score *= 1.6
            reasons.append("fresh (<7d)")
        elif age <= fresh:
            score *= 1.25
            reasons.append(f"{age}d old")
        elif age <= 120:
            score *= 0.8
            reasons.append(f"{age}d (aging)")
        else:
            score *= 0.45
            reasons.append(f"{age}d (stale)")

    stars = it.get("stars")
    if stars is not None:
        if stars >= 1000:
            score *= 1.15
            reasons.append(f"★{stars}")
        elif stars >= 100:
            score *= 1.05
            reasons.append(f"★{stars}")
        elif stars < 20:
            score *= 0.7
            reasons.append(f"★{stars} (small)")

    pushed = it.get("pushed_days")
    if pushed is not None:
        if pushed <= 30:
            reasons.append("active repo")
            score *= 1.1
        elif pushed > 365:
            score *= 0.5
            reasons.append(f"repo idle {pushed}d")

    if it.get("archived"):
        score *= 0.2
        reasons.append("archived")

    comments = it.get("comments")
    if comments and comments > 60 and it.get("source") == "github":
        score *= 0.6
        reasons.append(f"{comments} comments (maybe crowded)")

    # Freelancer-profile skill match (pure — do not mutate the item here)
    boost, hits = skill_boost(it, settings.get("profile") or "any")
    if hits:
        score *= boost
        reasons.append("skill match: " + ", ".join(hits[:3]))

    # Preflight quality (GO / CAUTION / STOP) — only when already attached
    pf = it.get("preflight") or {}
    if pf.get("verdict") == "STOP":
        score *= 0.25
        reasons.append("preflight STOP")
    elif pf.get("verdict") == "CAUTION":
        score *= 0.7
        reasons.append("preflight CAUTION")
    elif pf.get("verdict") == "GO":
        score *= 1.2
        reasons.append("preflight GO")
    if pf.get("open_prs") is not None:
        if pf["open_prs"] == 0:
            reasons.append("no competing PRs")
        elif pf["open_prs"] >= 1:
            reasons.append(f"{pf['open_prs']} open PR(s) on issue")

    return round(score, 1), reasons


def collect(settings, log, progress=None, known_repos=None):
    items = []
    # 1) GitHub first so we can discover Algora orgs mentioned in issue bodies.
    gh_items = scan_github(settings, log)
    items.extend(gh_items)

    # 2) Algora orgs: configured list + auto-discovered handles (capped).
    orgs = list(settings.get("orgs") or [])
    if settings.get("auto_discover_orgs", True):
        discovered = discover_algora_orgs(gh_items, log=log)
        for o in discovered:
            if o not in orgs:
                orgs.append(o)
        # Don't explode the request budget.
        orgs = orgs[: max(len(settings.get("orgs") or []), 24)]
    if orgs:
        if progress:
            progress(f"Scanning {len(orgs)} Algora orgs…")
        items.extend(scan_algora(orgs, settings, log).values())

    merged = {}
    for it in items:
        key = (it["repo"].lower(), it["number"])
        cur = merged.get(key)
        if cur is None:
            merged[key] = it
        else:
            if cur.get("amount") is None and it.get("amount") is not None:
                cur["amount"], cur["amount_estimated"] = it["amount"], it.get("amount_estimated", True)
            if cur.get("claims") is None and it.get("claims") is not None:
                cur["claims"] = it["claims"]
            if cur.get("age_days") is None:
                cur["age_days"], cur["age_text"] = it.get("age_days"), it.get("age_text")
            if "algora" == it.get("source"):
                cur["platform"] = "Algora"
            for k in ("comments", "labels", "stars"):
                if cur.get(k) in (None, [], "") and it.get(k) not in (None, [], ""):
                    cur[k] = it[k]

    keep = [it for it in merged.values() if not is_denied(it, settings)]
    log(f"[filter] {len(merged)} unique · dropped (fake/no-money): {len(merged) - len(keep)}")

    def pre(it):
        amt = it.get("amount")
        ok_amt = (amt is None) or (amt >= settings.get("min_amount", 0))
        age = it.get("age_days")
        ok_age = (age is None) or (age <= settings.get("max_age_days", 400))
        cl = it.get("claims")
        ok_cl = (cl is None) or (cl <= settings.get("max_claims", 999))
        return ok_amt and ok_age and ok_cl

    candidates = [it for it in keep if pre(it)]
    candidates.sort(key=lambda it: (it.get("amount") or 25) / (1.0 + (it.get("claims") or 3)),
                    reverse=True)
    if progress:
        progress("Enriching repositories…")
    enrich_limit = int(settings.get("enrich_limit", 20))
    enrich_repos(candidates[:max(enrich_limit * 2, 40)], settings, log,
                 limit=enrich_limit, known=known_repos)

    # Preflight quality on the strongest candidates (API-budget aware)
    if progress:
        progress("Preflight quality checks…")
    preflight_top_items(candidates, settings, log,
                        limit=int(settings.get("preflight_limit", 12) or 0),
                        known=known_repos)

    results = []
    for it in candidates:
        if settings.get("active_only") and it.get("pushed_days") and it["pushed_days"] > 90:
            continue
        s, reasons = score_item(it, settings)
        it["score"] = s
        it["why"] = " · ".join(reasons)
        _, hits = skill_boost(it, settings.get("profile") or "any")
        it["skill_hits"] = hits
        results.append(it)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


# ----------------------------------------------------------------------------- scan cache

_REPO_META_CACHE = {}


def _cache_key(settings):
    blob = {
        "profile": settings.get("profile"),
        "languages": settings.get("languages"),
        "min_amount": settings.get("min_amount"),
        "max_claims": settings.get("max_claims"),
        "max_age_days": settings.get("max_age_days"),
        "active_only": settings.get("active_only"),
        "hide_farms": settings.get("hide_farms"),
        "orgs": settings.get("orgs"),
        "use_github_search": settings.get("use_github_search"),
        "use_opire_bot": settings.get("use_opire_bot"),
    }
    return json.dumps(blob, sort_keys=True)


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass


def get_cached_results(settings):
    minutes = float(settings.get("cache_minutes") or 0)
    if minutes <= 0:
        return None
    cache = load_cache()
    key = _cache_key(settings)
    entry = cache.get(key)
    if not entry:
        return None
    try:
        ts = datetime.fromisoformat(entry["ts"])
    except Exception:
        return None
    age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
    if age_min > minutes:
        return None
    return entry.get("results") or None


def put_cached_results(settings, results):
    if float(settings.get("cache_minutes") or 0) <= 0:
        return
    cache = load_cache()
    key = _cache_key(settings)
    # Keep only a few entries so the file stays small.
    if len(cache) > 12:
        cache = dict(sorted(cache.items(), key=lambda kv: kv[1].get("ts", ""), reverse=True)[:8])
    cache[key] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "results": results[:80],
    }
    save_cache(cache)


def collect_smart(settings, log, progress=None):
    """Cached wrapper around collect() — skips the network when a fresh scan exists."""
    cached = get_cached_results(settings)
    if cached is not None:
        minutes = settings.get("cache_minutes", 5)
        log(f"[cache] using results from the last {minutes} min ({len(cached)} items)")
        if progress:
            progress("Loaded from cache")
        # Refresh is_new flags without treating this as a brand-new baseline.
        return cached, True
    results = collect(settings, log, progress=progress, known_repos=_REPO_META_CACHE)
    put_cached_results(settings, results)
    return results, False


# ----------------------------------------------------------------------------- stats

def summarize(results):
    """Dashboard numbers for the UI."""
    amounts = [r["amount"] for r in results if r.get("amount") is not None]
    low_comp = [r for r in results if (r.get("claims") is None or (r.get("claims") or 0) <= 2)]
    fresh = [r for r in results if (r.get("age_days") is not None and r["age_days"] <= 14)]
    skill = [r for r in results if r.get("skill_hits")]
    platforms = {}
    for r in results:
        p = r.get("platform") or "?"
        platforms[p] = platforms.get(p, 0) + 1
    return {
        "total": len(results),
        "total_money": round(sum(amounts), 0) if amounts else 0,
        "avg_money": round(sum(amounts) / len(amounts), 0) if amounts else 0,
        "known_amounts": len(amounts),
        "low_competition": len(low_comp),
        "fresh": len(fresh),
        "skill_matched": len(skill),
        "new": sum(1 for r in results if r.get("is_new")),
        "platforms": platforms,
        "top_score": results[0]["score"] if results else 0,
        "preflight_go": sum(1 for r in results if (r.get("preflight") or {}).get("verdict") == "GO"),
        "preflight_caution": sum(1 for r in results if (r.get("preflight") or {}).get("verdict") == "CAUTION"),
        "preflight_stop": sum(1 for r in results if (r.get("preflight") or {}).get("verdict") == "STOP"),
    }


# ----------------------------------------------------------------------------- console mode

def console_scan(argv):
    settings = load_settings()
    args, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a == "--scan":
            i += 1
            continue
        if a == "--no-search":
            settings["use_github_search"] = settings["use_opire_bot"] = False
            i += 1
            continue
        if a == "--no-orgs":
            settings["orgs"] = []
            i += 1
            continue
        if a == "--notify-test":
            settings["_notify_test"] = True
            i += 1
            continue
        if a == "--watch":
            args[a] = argv[i + 1] if i + 1 < len(argv) else "15"
            i += 2
            continue
        if a in ("--json", "--lang", "--profile", "--min-amount", "--max-claims", "--max-age",
                 "--enrich", "--orgs") and i + 1 < len(argv):
            args[a] = argv[i + 1]
            i += 2
            continue
        i += 1
    if "--profile" in args and args["--profile"] in PROFILES:
        settings["profile"] = args["--profile"]
        settings["languages"] = list(PROFILES[args["--profile"]]["languages"])
    if "--lang" in args:
        settings["languages"] = _LEGACY_LANG.get(args["--lang"], [])
    for key, skey, cast in (("--min-amount", "min_amount", float),
                            ("--max-claims", "max_claims", int),
                            ("--max-age", "max_age_days", int),
                            ("--enrich", "enrich_limit", int)):
        if key in args:
            settings[skey] = cast(args[key])
    if "--orgs" in args:
        settings["orgs"] = [o for o in args["--orgs"].split(",") if o]

    def log(msg):
        print("  · " + msg)

    if settings.pop("_notify_test", False):
        ok = notify("Bounty Radar", "Test notification from bounty_radar.py --notify-test", log=log)
        print("notification sent" if ok else "notification FAILED")
        return 0 if ok else 1

    if "--watch" in args:
        try:
            interval_min = max(0.1, float(args["--watch"]))
        except ValueError:
            interval_min = 15.0
        first = not load_seen()
        print(f"watch mode: rescanning every {interval_min:g} min"
              + (" (first pass records a baseline, no alerts)" if first else "") + " — Ctrl+C to stop")
        try:
            while True:
                res, from_cache = collect_smart(settings, log)
                n_new = mark_new(res, log)
                for it in [r for r in res if r.get("is_new")][:10]:
                    amt = "$?" if it.get("amount") is None else f"${it['amount']:.0f}"
                    print(f"  NEW  {amt:>7}  {it.get('repo_short', it['repo'].split('/')[-1])}"
                          f"#{it['number']}  {it['title'][:60]}\n        {it['url']}")
                if n_new:
                    notify_new_bounties([r for r in res if r.get("is_new")], log=log)
                time.sleep(interval_min * 60)
        except KeyboardInterrupt:
            print("\nwatch stopped")
        return 0

    results, from_cache = collect_smart(settings, log)
    prof = PROFILES.get(settings.get("profile") or "any", PROFILES["any"])
    print(f"\n=== {len(results)} bounties · profile: {prof['label']}"
          + (" · cached" if from_cache else "") + " ===")
    print(f"{'score':>6} {'$':>8} {'claims':>6} {'age':>5} {'skill':>5}  {'repo#issue':<34} title")
    for it in results[:25]:
        amt = "-" if it.get("amount") is None else f"{it['amount']:.0f}"
        cl = "-" if it.get("claims") is None else str(it["claims"])
        age = "-" if it.get("age_days") is None else str(it["age_days"])
        skill = str(len(it.get("skill_hits") or [])) or "-"
        tag = f"{it.get('repo_short', it['repo'].split('/')[-1])}#{it['number']}"
        print(f"{it['score']:>6} {amt:>8} {cl:>6} {age:>5} {skill:>5}  {tag[:34]:<34} {it['title'][:56]}")
        print(f"{'':>6} {it['url']}")
        print(f"{'':>6} why: {it['why'][:110]}")
    if "--json" in args:
        with open(args["--json"], "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nJSON saved -> {args['--json']}")
    return 0


# ----------------------------------------------------------------------------- web UI state

class AppState:
    """Shared, thread-safe state between the scanner worker and the HTTP API."""

    def __init__(self):
        self.lock = threading.RLock()
        self.settings = load_settings()
        self.results = []
        self.logs = []
        self.scanning = False
        self.status = "Ready"
        self.progress = 0
        self.from_cache = False
        self.watch_thread = None
        self.watch_running = False
        self.watch_left = 0
        self.scan_thread = None
        self.stop = False
        self.last_error = None
        self.stats = summarize([])

    def log(self, msg):
        with self.lock:
            stamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append(f"[{stamp}] {msg}")
            if len(self.logs) > 400:
                self.logs = self.logs[-300:]

    def snapshot(self):
        with self.lock:
            return {
                "scanning": self.scanning,
                "status": self.status,
                "progress": self.progress,
                "from_cache": self.from_cache,
                "watch": self.watch_running,
                "watch_left": self.watch_left,
                "logs": self.logs[-80:],
                "results": self.results,
                "stats": self.stats,
                "settings": _public_settings(self.settings),
                "profiles": [
                    {"id": p["id"], "label": p["label"], "icon": p["icon"], "desc": p["desc"]}
                    for p in PROFILES.values()
                ],
                "error": self.last_error,
            }


def _public_settings(s):
    """Settings safe to send to the browser (token stays server-side by default)."""
    out = dict(s)
    tok = out.get("token") or ""
    out["token"] = tok  # local app only; user owns this machine
    out["token_set"] = bool(tok)
    return out


APP = AppState()


def _start_scan_worker():
    if APP.scanning:
        return False
    APP.stop = False
    APP.last_error = None
    APP.from_cache = False
    settings = APP.settings
    profile = PROFILES.get(settings.get("profile") or "any", PROFILES["any"])

    def worker():
        APP.scanning = True
        APP.progress = 5
        APP.status = f"Scanning · {profile['label']}"
        APP.log(f"scan start · profile={profile['label']} · orgs={len(settings.get('orgs') or [])}")

        def progress(msg):
            APP.status = msg
            APP.progress = min(90, APP.progress + 8)

        def log(msg):
            APP.log(msg)

        try:
            results, from_cache = collect_smart(settings, log, progress=progress)
            if APP.stop:
                APP.status = "Stopped"
                APP.log("scan stopped by user")
            else:
                n_new = mark_new(results, log=log)
                APP.results = results
                APP.from_cache = from_cache
                APP.stats = summarize(results)
                APP.stats["new"] = n_new
                APP.progress = 100
                APP.status = (
                    f"Done · {len(results)} bounties"
                    + (f" · {n_new} new" if n_new else "")
                    + (" · cached" if from_cache else "")
                )
                APP.log(APP.status)
                if n_new and settings.get("watch"):
                    threading.Thread(
                        target=lambda: notify_new_bounties([r for r in results if r.get("is_new")]),
                        daemon=True,
                    ).start()
        except Exception as e:
            APP.last_error = str(e)
            APP.status = f"Error: {e}"
            APP.log(f"scan error: {e}")
        finally:
            APP.scanning = False

    APP.scan_thread = threading.Thread(target=worker, daemon=True)
    APP.scan_thread.start()
    return True


def _watch_loop():
    while APP.watch_running:
        minutes = max(1.0, float(APP.settings.get("watch_minutes") or 15))
        total = int(minutes * 60)
        for remaining in range(total, 0, -1):
            if not APP.watch_running:
                return
            APP.watch_left = remaining
            if remaining % 5 == 0:
                mm, ss = divmod(remaining, 60)
                APP.status = f"Watching · next scan in {mm:02d}:{ss:02d}"
            time.sleep(1)
        if APP.watch_running and not APP.scanning:
            APP.log("watch tick → rescan")
            _start_scan_worker()
            # Wait for the scan to finish before the next countdown.
            while APP.watch_running and APP.scanning:
                time.sleep(1)


def set_watch(on: bool):
    if on:
        if APP.watch_running:
            return
        APP.watch_running = True
        APP.settings["watch"] = True
        save_settings(APP.settings)
        APP.log(f"watch ON · every {APP.settings.get('watch_minutes', 15)} min")
        if not APP.scanning and not APP.results:
            _start_scan_worker()
        threading.Thread(target=_watch_loop, daemon=True).start()
    else:
        APP.watch_running = False
        APP.settings["watch"] = False
        save_settings(APP.settings)
        APP.status = "Watch stopped"
        APP.log("watch OFF")


# ----------------------------------------------------------------------------- web server

def _load_ui_html():
    try:
        with open(UI_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return _FALLBACK_HTML


def _json_body(handler):
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


class RadarHandler(BaseHTTPRequestHandler):
    server_version = "BountyRadar/2.0"

    def log_message(self, fmt, *args):
        return  # keep the console quiet; the app logs its own work

    def _send(self, code=200, body=b"", ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, data, "application/json; charset=utf-8")

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, _load_ui_html().encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/state":
            self._json(APP.snapshot())
            return
        if path == "/api/export/csv":
            if not APP.results:
                self._json({"ok": False, "error": "no results yet"}, 400)
                return
            path_csv = os.path.join(APP_DIR, "bounties.csv")
            with open(path_csv, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["score", "amount", "claims", "age_days", "repo", "number",
                            "title", "platform", "url", "why", "skill_hits"])
                for it in APP.results:
                    w.writerow([
                        it.get("score"), it.get("amount"), it.get("claims"), it.get("age_days"),
                        it["repo"], it.get("number"), it.get("title"), it.get("platform", ""),
                        it.get("url", ""), it.get("why", ""),
                        ",".join(it.get("skill_hits") or []),
                    ])
            self._json({"ok": True, "path": path_csv})
            return
        if path == "/api/notify-test":
            ok = notify("Bounty Radar", "Test notification — alerts are working")
            self._json({"ok": ok})
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        body = _json_body(self)
        if path == "/api/scan":
            # Optional: apply a quick profile switch before scanning.
            if "profile" in body and body["profile"] in PROFILES:
                APP.settings["profile"] = body["profile"]
                APP.settings["languages"] = list(PROFILES[body["profile"]]["languages"])
                save_settings(APP.settings)
            for key, cast in (("min_amount", float), ("max_claims", int),
                              ("max_age_days", int), ("watch_minutes", float),
                              ("cache_minutes", float), ("enrich_limit", int),
                              ("preflight_limit", int)):
                if key in body:
                    try:
                        APP.settings[key] = cast(body[key])
                    except (TypeError, ValueError):
                        pass
            if "active_only" in body:
                APP.settings["active_only"] = bool(body["active_only"])
            if "hide_farms" in body:
                APP.settings["hide_farms"] = bool(body["hide_farms"])
            if "auto_discover_orgs" in body:
                APP.settings["auto_discover_orgs"] = bool(body["auto_discover_orgs"])
            if "token" in body:
                APP.settings["token"] = (body.get("token") or "").strip()
            if "orgs" in body and isinstance(body["orgs"], list):
                APP.settings["orgs"] = [str(o).strip().lstrip("@") for o in body["orgs"] if str(o).strip()]
            save_settings(APP.settings)
            started = _start_scan_worker()
            self._json({"ok": True, "started": started})
            return
        if path == "/api/settings":
            for key, cast in (("min_amount", float), ("max_claims", int),
                              ("max_age_days", int), ("watch_minutes", float),
                              ("cache_minutes", float), ("enrich_limit", int),
                              ("preflight_limit", int)):
                if key in body:
                    try:
                        APP.settings[key] = cast(body[key])
                    except (TypeError, ValueError):
                        pass
            if "profile" in body and body["profile"] in PROFILES:
                APP.settings["profile"] = body["profile"]
                if not body.get("keep_languages"):
                    APP.settings["languages"] = list(PROFILES[body["profile"]]["languages"])
            if "token" in body:
                APP.settings["token"] = (body.get("token") or "").strip()
            if "active_only" in body:
                APP.settings["active_only"] = bool(body["active_only"])
            if "hide_farms" in body:
                APP.settings["hide_farms"] = bool(body["hide_farms"])
            if "auto_discover_orgs" in body:
                APP.settings["auto_discover_orgs"] = bool(body["auto_discover_orgs"])
            if "orgs" in body and isinstance(body["orgs"], list):
                APP.settings["orgs"] = [str(o).strip().lstrip("@") for o in body["orgs"] if str(o).strip()]
            save_settings(APP.settings)
            self._json({"ok": True, "settings": _public_settings(APP.settings)})
            return
        if path == "/api/watch":
            set_watch(bool(body.get("on")))
            self._json({"ok": True, "watch": APP.watch_running})
            return
        if path == "/api/stop":
            APP.stop = True
            self._json({"ok": True})
            return
        self._json({"error": "not found"}, 404)


def _find_free_port(preferred=8765):
    for port in range(preferred, preferred + 20):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            s.close()
    return 0


def run_web_ui(port=8765, open_browser=True):
    port = _find_free_port(port)
    if not port:
        print("Could not bind a local port. Try closing other Bounty Radar windows.")
        return 1
    url = f"http://127.0.0.1:{port}/"
    print("Bounty Radar Pro")
    print(f"  UI:  {url}")
    print("  Stop: close this window or press Ctrl+C")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    if APP.settings.get("watch"):
        threading.Thread(target=lambda: set_watch(True), daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", port), RadarHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        APP.watch_running = False
        server.server_close()
    return 0


# Minimal page if ui/index.html is missing
_FALLBACK_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Bounty Radar Pro</title>
<style>body{background:#0B1220;color:#E2E8F0;font:14px/1.5 system-ui,sans-serif;padding:40px}
button{background:#10B981;color:#042f2e;border:0;border-radius:8px;padding:10px 16px;font-weight:600;cursor:pointer}
code{background:#1E293B;padding:2px 6px;border-radius:4px}</style></head>
<body><h1>Bounty Radar Pro</h1>
<p>UI file missing. Put <code>ui/index.html</code> next to this script, or use CLI:</p>
<p><code>python bounty_radar.py --scan --profile frontend</code></p>
<button onclick="fetch('/api/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})">Scan now</button>
<script>
setInterval(async()=>{const s=await (await fetch('/api/state')).json();
document.body.querySelector('p')?.setAttribute('data-x',s.status)},1000)
</script></body></html>"""


# ----------------------------------------------------------------------------- Tkinter GUI

UNICODE_OK = [True]


def T(fa, en):
    return fa if UNICODE_OK[0] else en


def enable_unicode(root):
    try:
        root.tk.call("encoding", "system", "utf-8")
        root.tk.call("set", "br_probe", "آزمایش")
        return True
    except Exception:
        UNICODE_OK[0] = False
        return False


def run_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox

    settings = load_settings()
    root = tk.Tk()
    enable_unicode(root)
    root.title("Bounty Radar Pro")
    root.geometry("1280x760")
    try:
        root.configure(bg="#0B1220")
    except Exception:
        pass

    log_queue = queue.Queue()
    result_queue = queue.Queue()

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(".", background="#0B1220", foreground="#E2E8F0", fieldbackground="#1E293B")
    style.configure("TFrame", background="#0B1220")
    style.configure("TLabel", background="#0B1220", foreground="#E2E8F0")
    style.configure("TButton", background="#1E293B", foreground="#E2E8F0", padding=6)
    style.map("TButton", background=[("active", "#334155")])
    style.configure("Accent.TButton", background="#10B981", foreground="#042f2e")
    style.map("Accent.TButton", background=[("active", "#34D399")])
    style.configure("Treeview", background="#111827", fieldbackground="#111827",
                    foreground="#E2E8F0", rowheight=26)
    style.configure("Treeview.Heading", background="#1E293B", foreground="#94A3B8")
    style.map("Treeview", background=[("selected", "#065F46")])

    # ---- profile row
    pbar = ttk.Frame(root, padding=8)
    pbar.pack(fill="x")
    ttk.Label(pbar, text="Profile:").pack(side="left")
    profile_var = tk.StringVar(value=settings.get("profile") or "any")
    prof_labels = [f"{p['icon']} {p['label']}" for p in PROFILES.values()]
    prof_ids = [p["id"] for p in PROFILES.values()]
    if settings.get("profile") in prof_ids:
        profile_var.set(f"{PROFILES[settings['profile']]['icon']} {PROFILES[settings['profile']]['label']}")

    def on_profile(_e=None):
        sel = profile_var.get()
        for p in PROFILES.values():
            if sel == f"{p['icon']} {p['label']}" or sel == p["id"] or sel == p["label"]:
                APP.settings["profile"] = p["id"]
                APP.settings["languages"] = list(p["languages"])
                save_settings(APP.settings)
                status_var.set(f"Profile → {p['label']} ({p['desc']})")
                return

    ttk.Combobox(pbar, textvariable=profile_var, values=prof_labels, width=28,
                 state="readonly").pack(side="left", padx=6)
    profile_var.trace_add("write", lambda *_: on_profile())

    def mk_button(text, cmd, accent=False):
        b = ttk.Button(pbar, text=text, command=cmd,
                       style="Accent.TButton" if accent else "TButton")
        b.pack(side="left", padx=3)
        return b

    btn_find = mk_button("Scan bounties", lambda: start_scan(), accent=True)
    btn_open = mk_button("Open", lambda: open_selected())
    btn_copy = mk_button("Copy link", lambda: copy_selected())
    btn_csv = mk_button("CSV", lambda: save_csv())
    btn_web = mk_button("Open Web UI", lambda: threading.Thread(
        target=lambda: run_web_ui(open_browser=True), daemon=True).start())

    # ---- filters
    fbar = ttk.Frame(root, padding=(8, 0))
    fbar.pack(fill="x")
    min_amt_var = tk.StringVar(value=str(int(settings["min_amount"])))
    ttk.Label(fbar, text="Min $:").pack(side="left")
    ttk.Entry(fbar, textvariable=min_amt_var, width=6).pack(side="left", padx=(2, 10))
    max_claims_var = tk.StringVar(value=str(settings["max_claims"]))
    ttk.Label(fbar, text="Max claims:").pack(side="left")
    ttk.Entry(fbar, textvariable=max_claims_var, width=5).pack(side="left", padx=(2, 10))
    max_age_var = tk.StringVar(value=str(settings["max_age_days"]))
    ttk.Label(fbar, text="Max age:").pack(side="left")
    ttk.Entry(fbar, textvariable=max_age_var, width=6).pack(side="left", padx=(2, 10))
    active_var = tk.BooleanVar(value=settings["active_only"])
    ttk.Checkbutton(fbar, text="Active repos only", variable=active_var).pack(side="left", padx=4)
    farms_var = tk.BooleanVar(value=settings["hide_farms"])
    ttk.Checkbutton(fbar, text="Hide fake bounties", variable=farms_var).pack(side="left", padx=4)

    wbar = ttk.Frame(root, padding=(8, 2))
    wbar.pack(fill="x")
    watch_var = tk.BooleanVar(value=bool(settings.get("watch", False)))
    ttk.Checkbutton(wbar, text="Watch every", variable=watch_var,
                    command=lambda: toggle_watch()).pack(side="left")
    watch_min_var = tk.StringVar(value=str(settings.get("watch_minutes", 15)))
    ttk.Entry(wbar, textvariable=watch_min_var, width=4).pack(side="left", padx=3)
    ttk.Label(wbar, text="minutes · re-scan and flag new bounties").pack(side="left")
    ttk.Button(wbar, text="Test alert", command=lambda: test_notify()).pack(side="left", padx=8)

    tbar = ttk.Frame(root, padding=(8, 4))
    tbar.pack(fill="x")
    token_var = tk.StringVar(value=settings.get("token", ""))
    ttk.Label(tbar, text="GitHub token (optional):").pack(side="left")
    ttk.Entry(tbar, textvariable=token_var, width=48, show="*").pack(side="left", padx=4)
    ttk.Label(tbar, text="Works without it — slower, fewer results.").pack(side="left")

    # ---- stats strip
    stats_var = tk.StringVar(value="No results yet")
    ttk.Label(root, textvariable=stats_var, padding=(10, 4)).pack(fill="x")

    cols = ("score", "amount", "claims", "age", "skill", "repo", "title", "platform", "why")
    table = ttk.Treeview(root, columns=cols, show="headings", height=18)
    for c, t, w in (("score", "score", 60), ("amount", "$", 70), ("claims", "claims", 60),
                    ("age", "days", 50), ("skill", "match", 60), ("repo", "repo#issue", 220),
                    ("title", "title", 300), ("platform", "platform", 90),
                    ("why", "why this rank?", 280)):
        table.heading(c, text=t)
        table.column(c, width=w, anchor="w")
    table.pack(fill="both", expand=True, padx=8)
    try:
        table.tag_configure("new", background="#064E3B", foreground="#A7F3D0")
        table.tag_configure("hot", background="#1E293B", foreground="#5EEAD4")
    except Exception:
        pass

    status_var = tk.StringVar(value="Ready. Pick a profile and click Scan.")
    ttk.Label(root, textvariable=status_var, anchor="w", padding=(10, 4)).pack(fill="x")
    log_box = tk.Text(root, height=5, wrap="word", bg="#0F172A", fg="#94A3B8")
    log_box.pack(fill="x", padx=8, pady=(0, 8))

    state = {"thread": None, "stop": False, "results": [], "scanning": False,
             "watching": False, "watch_minutes": float(settings.get("watch_minutes", 15) or 15)}

    def log(msg):
        log_queue.put(msg)

    def pump_log():
        try:
            while True:
                msg = log_queue.get_nowait()
                try:
                    log_box.insert("end", msg + "\n")
                except Exception:
                    log_box.insert("end", "[log entry could not be displayed]\n")
                log_box.see("end")
        except queue.Empty:
            pass
        root.after(200, pump_log)

    def pump_results():
        try:
            while True:
                kind, payload = result_queue.get_nowait()
                if kind == "status":
                    status_var.set(payload)
                elif kind == "scan_request":
                    start_scan(clear_log=False)
                elif kind == "done":
                    results, n_new = payload if isinstance(payload, tuple) else (payload, 0)
                    state["results"] = results
                    render(results)
                    st = summarize(results)
                    stats_var.set(
                        f"{st['total']} bounties · ${st['total_money']:,.0f} known · "
                        f"{st['fresh']} fresh · {st['low_competition']} low-competition · "
                        f"{st['skill_matched']} skill matches"
                        + (f" · {n_new} NEW" if n_new else "")
                    )
                    note = f" | NEW {n_new}" if n_new else ""
                    status_var.set(f"Done: {len(results)} bounties.{note}")
                    btn_find.state(["!disabled"])
                    if n_new and state.get("watching"):
                        threading.Thread(
                            target=lambda: notify_new_bounties([r for r in results if r.get("is_new")]),
                            daemon=True).start()
                elif kind == "error":
                    status_var.set(payload)
                    btn_find.state(["!disabled"])
                    messagebox.showwarning("Bounty Radar", payload)
        except queue.Empty:
            pass
        root.after(200, pump_results)

    def render(items):
        table.delete(*table.get_children())
        for it in items:
            amt = "?" if it.get("amount") is None else f"${it['amount']:.0f}"
            cl = "?" if it.get("claims") is None else str(it["claims"])
            age = "?" if it.get("age_days") is None else str(it["age_days"])
            skill = str(len(it.get("skill_hits") or [])) if it.get("skill_hits") else "-"
            mark = "NEW " if it.get("is_new") else ""
            tags = ("new",) if it.get("is_new") else (("hot",) if it.get("skill_hits") else ())
            table.insert("", "end", tags=tags, values=(
                mark + str(it["score"]), amt, cl, age, skill,
                f"{it.get('repo_short', it['repo'].split('/')[-1])}#{it['number']}",
                it["title"][:90], it.get("platform", ""), it["why"]))

    def current_settings():
        s = load_settings()
        s["token"] = token_var.get().strip()
        # Keep the selected profile's languages.
        prof = PROFILES.get(s.get("profile") or "any", PROFILES["any"])
        s["languages"] = list(prof["languages"])
        for var, key, cast in ((min_amt_var, "min_amount", float),
                               (max_claims_var, "max_claims", int),
                               (max_age_var, "max_age_days", int)):
            try:
                s[key] = cast(var.get())
            except ValueError:
                pass
        s["active_only"] = active_var.get()
        s["hide_farms"] = farms_var.get()
        s["watch"] = watch_var.get()
        try:
            s["watch_minutes"] = max(1.0, float(watch_min_var.get()))
        except ValueError:
            s["watch_minutes"] = 15
        save_settings(s)
        APP.settings = s
        return s

    def start_scan(clear_log=True):
        if state.get("scanning"):
            return
        s = current_settings()
        table.delete(*table.get_children())
        if clear_log:
            log_box.delete("1.0", "end")
        state["stop"] = False
        state["scanning"] = True
        btn_find.state(["disabled"])
        status_var.set("Searching…")

        def worker():
            try:
                log(f"profile: {s.get('profile')} · orgs: {', '.join(s['orgs'][:8])}")
                res, from_cache = collect_smart(s, log)
                n_new = mark_new(res, log)
                result_queue.put(("done", (res, n_new)))
            except Exception as e:
                result_queue.put(("error", f"Error: {e}"))
            finally:
                state["scanning"] = False

        state["thread"] = threading.Thread(target=worker, daemon=True)
        state["thread"].start()

    def watch_loop():
        while state.get("watching"):
            interval = int(max(1.0, state.get("watch_minutes", 15)) * 60)
            for remaining in range(interval, 0, -1):
                if not state.get("watching"):
                    return
                if remaining % 5 == 0:
                    result_queue.put(("status", f"Watching · next scan in {remaining // 60:02d}:{remaining % 60:02d}"))
                time.sleep(1)
            if state.get("watching"):
                result_queue.put(("scan_request", None))

    def toggle_watch():
        if watch_var.get():
            try:
                state["watch_minutes"] = max(1.0, float(watch_min_var.get()))
            except ValueError:
                state["watch_minutes"] = 15
                watch_min_var.set("15")
            state["watching"] = True
            log(f"[watch] ON — every {state['watch_minutes']:.0f} min")
            start_scan(clear_log=False)
            threading.Thread(target=watch_loop, daemon=True).start()
        else:
            state["watching"] = False
            status_var.set("Watch stopped.")

    def test_notify():
        def job():
            ok = notify("Bounty Radar", "Test notification — if you can see this, alerts work")
            log("[notify] " + ("sent" if ok else "delivery failed"))
        threading.Thread(target=job, daemon=True).start()

    def selected():
        sel = table.selection()
        if not sel:
            messagebox.showinfo("Bounty Radar", "Select a row first.")
            return None
        values = table.item(sel[0], "values")
        repo_issue = values[5]
        for it in state["results"]:
            short = it.get("repo_short", it["repo"].split("/")[-1])
            if f"{short}#{it['number']}" == repo_issue:
                return it
        return None

    def open_selected():
        it = selected()
        if it:
            webbrowser.open(it["url"])

    def copy_selected():
        it = selected()
        if it:
            root.clipboard_clear()
            root.clipboard_append(it["url"])
            status_var.set("Link copied: " + it["url"])

    def save_csv():
        if not state["results"]:
            return
        path = os.path.join(APP_DIR, "bounties.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["score", "amount", "claims", "age_days", "repo", "number",
                        "title", "platform", "url", "why", "skill_hits"])
            for it in state["results"]:
                w.writerow([it["score"], it.get("amount"), it.get("claims"), it.get("age_days"),
                            it["repo"], it["number"], it["title"], it.get("platform", ""),
                            it["url"], it["why"], ",".join(it.get("skill_hits") or [])])
        status_var.set("CSV saved: " + path)

    def on_close():
        state["watching"] = False
        try:
            current_settings()
        except Exception:
            pass
        root.destroy()

    table.bind("<Double-1>", lambda e: open_selected())
    root.protocol("WM_DELETE_WINDOW", on_close)
    pump_log()
    pump_results()
    if watch_var.get():
        root.after(500, toggle_watch)
    root.mainloop()
    return 0


# ----------------------------------------------------------------------------- main

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    argv = sys.argv[1:]
    if any(a in argv for a in ("--scan", "--watch", "--notify-test")):
        return console_scan(argv)
    if "--tk" in argv:
        return run_gui()
    # Default: modern web UI
    port = 8765
    for i, a in enumerate(argv):
        if a == "--port" and i + 1 < len(argv):
            try:
                port = int(argv[i + 1])
            except ValueError:
                pass
    return run_web_ui(port=port, open_browser="--no-browser" not in argv)


if __name__ == "__main__":
    sys.exit(main())

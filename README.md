# Bounty Radar Pro

[![CI](https://github.com/mohsen-niksirat/BountyRadar/actions/workflows/ci.yml/badge.svg)](https://github.com/mohsen-niksirat/BountyRadar/actions/workflows/ci.yml)
[![Pages](https://img.shields.io/badge/GitHub%20Pages-docs%2F-22d3ee)](https://github.com/mohsen-niksirat/BountyRadar/tree/main/docs)

Local Windows app that finds **paid freelance & open-source bounties** for **any** freelancer type — frontend, backend, mobile, data/ML, DevOps, security, docs/writing, design, full-stack.

**Live site (static preview):** after enabling Pages → `https://mohsen-niksirat.github.io/BountyRadar/`

No install, no paid APIs. Pure Python 3 + stdlib (`tkinter`, `urllib`, `json`, `http.server`).

## Run

**Double-click `Bounty Radar.bat`** → modern dark web UI opens in your browser (`http://127.0.0.1:8765/`).

Or from this folder:

```bash
python bounty_radar.py              # web UI (default)
python bounty_radar.py --tk         # classic Tkinter window
python bounty_radar.py --scan --profile frontend
python bounty_radar.py --watch 15   # background watch + Windows toast
python bounty_radar.py --notify-test
```

Optional flags: `--port 8765`, `--no-browser`.

## Freelancer profiles

| Profile | Best for |
|---|---|
| **Any** | No filter — widest net |
| **Frontend** | React, Vue, CSS, a11y, design systems |
| **Backend** | APIs, databases, Python/Go/Rust/Java |
| **Mobile** | iOS, Android, Flutter, React Native |
| **Data / ML** | ETL, models, analytics, notebooks |
| **DevOps** | CI/CD, Docker, K8s, cloud |
| **Security** | AppSec, audits, hardening |
| **Docs / Writing** | Docs, tutorials, translation, i18n |
| **Design** | UI/UX, icons, branding, Figma |
| **Full-stack** | End-to-end web apps |

Each profile drives GitHub search languages **and** a keyword skill-match boost. Results that hit profile keywords get a cyan “match” tag and rank higher — and the **why** column lists the exact keywords.

## Watch mode (where the money is)

Old open bounties are leftovers. Fresh ones with 0–2 claims are the real opportunity.

1. Turn **Watch** on (web UI or Tkinter).
2. First scan is a **silent baseline** — no alert spam.
3. Every N minutes it re-scans; new items get a green highlight + one consolidated Windows toast.
4. `seen.json` remembers what you’ve already seen across restarts.

## Data sources (public only)

| Source | Gives you | How |
|---|---|---|
| Algora org pages | **Real $ + claim counts** | `algora.io/<org>/bounties` |
| GitHub Search | `💎 Bounty`, `💰 Reward`, `label:bounty`, Opire bot comments | `/search/issues` |
| GitHub REST | Stars / activity / archived (top candidates only) | `/repos/<owner>/<name>` |

Default orgs (edit in Settings or `settings.json`): tscircuit, drizzle-team, cal, triggerdotdev, highlight, maybe-finance, twentyhq, novuhq, refinedev, unkeyed, and more.

## Scoring (explainable, no magic)

```
score = amount ÷ (1 + claims)
        × freshness     (≤7d: 1.6 · ≤30d: 1.25 · ≥120d: 0.45)
        × repo quality  (★≥1000: 1.15 · active: 1.1 · archived: 0.2)
        × skill match   (profile keywords, up to 1.45)
        × preflight     (GO 1.2 · CAUTION 0.7 · STOP 0.25)
        × penalties     (>60 comments: 0.6 · no stars: 0.7)
```

**Preflight** (top-N candidates, budget-aware) checks competing PRs, whether the
repo merges external PRs, issue open/locked state, and acceptance-criteria
heuristics — then labels the bounty **GO / CAUTION / STOP**.

Unknown amount is assumed $25×0.8 so known-dollar bounties stay on top.

## Efficiency

- **Result cache** (default 5 min) — identical filter sets skip the network.
- **Repo meta cache** — stars/activity are reused across scans in one session.
- **Profile-scoped queries** — only the searches your profile needs.
- **Auto-discovered Algora orgs** from GitHub issue links (capped).
- **Date-partitioned searches** to stay under GitHub’s 1000-result cap.
- **Fake-bounty filter** on by default (farms, $0, absurd amounts, airdrop/wallet scams).

## GitHub token (optional)

Without a token: 10 search/min, 60 core req/hour.  
With a token: 30 search/min, 5,000 core req/hour.

Create at <https://github.com/settings/tokens> — **no scopes needed** (public read only). Paste it in Settings. Stored locally in `settings.json`.

## Tests

```bash
python test_bounty_radar.py
```

Offline only — no network, no rate-limit burn. Covers Algora parser, aggregation, fake filters, scoring, profiles/skill-match, watch baseline, and summaries.

## Honest limits

- Opire amounts often live only on Opire (GitHub shows “amount unknown”).
- Claim counts are reliable mainly for Algora.
- Many GitHub “bounty” labels are spam — keep the fake filter on.
- Run daily; watch mode is the high-value path.

## Files

```
BountyRadar/
  bounty_radar.py       # engine + CLI + web server + Tk fallback
  ui/index.html         # local modern dark UI
  docs/index.html       # GitHub Pages static landing + demo
  docs/404.html
  Bounty Radar.bat      # double-click launcher
  test_bounty_radar.py  # offline tests
  ROADMAP.md            # phased delivery plan
  .github/workflows/    # CI + Pages deploy
  settings.json         # your filters / token / orgs (created on first save)
  seen.json             # watch-mode memory
  scan_cache.json       # short-lived scan cache
  scan_history.json     # rolling scan snapshots
```

## GitHub Pages (public preview site)

The `docs/` folder is a static marketing/demo page (sample data only — no live scan).

1. Repo **Settings → Pages**
2. **Build and deployment → Source: GitHub Actions**
3. Push to `main` (or run the *Deploy GitHub Pages* workflow)
4. Site URL: `https://mohsen-niksirat.github.io/BountyRadar/`

Workflow file: `.github/workflows/pages.yml` (deploys `docs/` automatically).

## Keyboard (web UI)

| Key | Action |
|-----|--------|
| `S` | Scan |
| `W` | Toggle watch |
| `/` | Focus search |
| `E` | Export CSV |
| `Esc` | Close drawer/modal |

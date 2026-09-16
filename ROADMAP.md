# Roadmap — Bounty Radar Pro

Phased plan to raise efficiency and quality. Each phase is independently shippable and pushed to `main`.

## Phase 1 — Foundation ✅
- Modern dark web UI + 10 freelancer profiles
- Explainable scoring + skill-match boost
- Result cache + repo meta cache
- Offline test suite, MIT license, GitHub Actions CI
- Research + preflight checklist in `docs/`

## Phase 2 — Preflight quality engine ✅
- Automated checklist signals: competing PRs, external-merge history, issue state
- Acceptance-criteria / thin-body heuristics
- GO / CAUTION / STOP verdicts boost or bury scores
- Preflight badges + factors in the web UI
- Top-N budget-aware checks (`preflight_limit`)

## Phase 3 — Smarter discovery ✅
- Auto-discover Algora org handles from GitHub issue bodies
- Date-partitioned search queries (1000-result cap)
- `/bounty $` and `/reward` command amount extraction
- GitHub-first scan order with capped org expansion

## Phase 4 — UI/UX quality ✅
- Filter chips: GO / fresh / low-competition / skill / new / $100+
- Score-breakdown drawer (“Why”)
- Keyboard: `/` search · `S` scan · `W` watch · `E` CSV · `Esc` close
- Auto-discover orgs toggle in Settings

## Phase 5 — Hardening ✅
- Expanded fake/scam deny-list (wallet/airdrop/private-key patterns)
- Rolling scan history (`scan_history.json`, `/api/history`)
- Markdown shortlist export (`/api/export/md`)
- Docs + CI + contributor-ready repo layout

## Possible next (not yet scheduled)
- Sparkline of last N scores per bounty
- Maintainer first-response median (needs more API budget)
- Optional local SQLite for multi-week history
- Packaging: `pyinstaller` one-file Windows binary

## Non-goals
- Paid APIs
- Mirroring full GitHub personal data
- Security-disclosure catalogs (HackerOne) mixed into bounty lists

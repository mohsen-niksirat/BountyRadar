# Roadmap — Bounty Radar Pro

Phased plan to raise efficiency and quality. Each phase is independently shippable and pushed to `main`.

## Phase 1 — Foundation (ship / polish)
- [x] Modern dark web UI + 10 freelancer profiles
- [x] Explainable scoring + skill-match boost
- [x] Result cache + repo meta cache
- [x] Offline test suite
- [x] MIT license, `.gitignore`, GitHub Actions CI
- [x] Research + preflight checklist in `docs/`

## Phase 2 — Preflight quality engine
- Integrate the 9-point preflight checklist into scoring
- Detect linked competing PRs on a bounty issue
- Detect whether the repo actually merges external PRs
- Surface a **Preflight** badge + score in the UI (go / caution / stop)
- Explain preflight factors in the "why" column

## Phase 3 — Smarter discovery (efficiency)
- Auto-discover Algora org handles from GitHub issue bodies/links
- Broader GitHub queries (date partitions, `/bounty $` comment signals)
- Better `$amount` extraction from titles + bodies + bot comments
- Parallel-safe Algora org fetch with shared throttle
- Rate-limit budget display in the UI

## Phase 4 — UI/UX quality
- Score breakdown drawer (every multiplier)
- Filter chips: platform / fresh / low-competition / skill-match / preflight
- Preflight badges on cards and table rows
- Keyboard: `/` search, `S` scan, `W` watch, `E` export
- Empty / error / rate-limit states that teach the user what to do

## Phase 5 — Hardening
- Expand deny-list + heuristics for fake bounties
- Persist scan history (last 50) for "what changed"
- Export markdown shortlist
- README screenshots + contributor guide

## Non-goals
- Paid APIs
- Mirroring full GitHub personal data
- Security-disclosure catalogs (HackerOne) mixed into bounty lists

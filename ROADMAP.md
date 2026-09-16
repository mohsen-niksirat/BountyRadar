# Roadmap — Bounty Radar Pro

Phased plan to raise efficiency and quality. Each phase is independently shippable and pushed to `main`.

## Delivered
- Phase 1–5: foundation, preflight, discovery, first UI pass, hardening (see git history)
- GitHub Pages landing (`docs/`)

## Phase 6 — Filter & sort system (UI)
- [x] Multi-select filter chips (GO / fresh / low-competition / skill / new / $100+ / caution / stop)
- [x] Platform multi-select (Algora / Opire / GitHub)
- [x] Client-side amount range
- [x] Sort field + ascending/descending toggle
- [x] Active-filter bar with count + Clear all
- [x] Debounced search

## Phase 7 — Pagination & card layout
- [x] Page size (12 / 24 / 48 / All) + prev/next + page numbers
- [x] Results header: showing X–Y of N (filtered / total)
- [x] Comfortable vs Compact card density
- [x] Equal-height cards, cleaner score row, platform chip first
- [x] Table view paginated the same way
- [x] Keyboard: `←` `→` page, `D` density

## Phase 8 — Layout polish (next)
- [ ] Sticky results toolbar
- [ ] Collapse sidebar on small screens
- [ ] Persist view/sort/pageSize in localStorage
- [ ] Column sort on table headers

## Phase 9 — Product depth (later)
- [ ] Sparkline of last N scores
- [ ] Maintainer first-response median
- [ ] Optional SQLite multi-week history
- [ ] One-file Windows package (PyInstaller)

## Non-goals
- Paid APIs
- Mirroring full GitHub personal data
- Security-disclosure catalogs mixed into bounty lists

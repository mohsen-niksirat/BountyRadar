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

## Phase 8 — Layout polish ✅
- [x] Sticky results toolbar
- [x] Collapse sidebar (☰, persisted)
- [x] Persist view/sort/density/pageSize in localStorage
- [x] Column sort on table headers
- [x] Hide STOP by default (toggle)
- [x] UI poll fingerprint — skip DOM rebuild when unchanged
- [x] Slim cached results (drop body)
- [x] Version + last-scan time in header
- [x] Better empty/scanning states; hide empty log

## Phase 10 — Product ship ✅
- [x] Standalone Windows packaging (`build_exe.py` / `build.bat` / PyInstaller onedir + onefile)
- [x] Frozen path handling (writable state next to exe, UI from bundle)
- [x] Claim workflow: shortlist → working → submitted → won/abandoned
- [x] Preflight checklist + notes per claim (`claims.json`)
- [x] ★ My claims filter + claim chips on cards
- [x] API `/api/claims` + tests

## Phase 11 — Optional next
- [ ] Tray icon / start with Windows
- [ ] Daily digest of top 5 (not only “new”)
- [ ] Offline demo mode with sample data

## Non-goals
- Paid APIs
- Mirroring full GitHub personal data
- Security-disclosure catalogs mixed into bounty lists

# Research Report: Open-Source Bounty Aggregator & Developer Matching Platform

**Research date:** 2026-09-17
**Report status:** Phase-0 feasibility research. No code written, no prototype built (per the brief).
**Verification level:** Every factual claim below is tagged `[VERIFIED]` (retrieved from a primary source during this session, with the retrieval shown), `[SECONDARY]` (retrieved from a third party), or `[UNVERIFIED]` / `[COULD NOT CONFIRM]`.

---

## Method & Limitations (read this before trusting any number)

**What was used.** Primary sources were retrieved directly (platform homepages, sitemaps, `robots.txt`, legal pages, public GitHub repositories, live HTTP/API endpoints, official GitHub docs, official HackerOne API docs). GitHub's own REST search API was used as a measurement instrument, which means the counts below are *actual API responses returned on 2026-09-17*, not estimates.

**What was NOT available in this research environment (important):**

| Capability | Status | Consequence |
|---|---|---|
| General web search engine (`web_search` tool) | **Failed for every query** | Broad keyword/demand research had to be done via an HTML search endpoint (DuckDuckGo Lite) and via GitHub's API instead |
| Reddit (`www.reddit.com`) | **Blocked** — DNS resolves to a reserved address (`10.10.34.35`) | Community complaints could **not** be directly quoted |
| Hacker News (Algolia API + hnrss.org) | **403 / 502** | HN threads could **not** be retrieved |
| Google Trends / SEO keyword volume | Not reachable | **No search-volume data exists in this report.** Any claim about "people search for this" is unsupported |
| `opire.dev`, `boss.dev`, `bountysource.com` | TCP connection closed / unresolved in this environment | Status of Opire and Boss.dev is **UNVERIFIED** in this report |
| package registry search (npm) | Timed out | Tool discovery via npm was incomplete |

**Therefore:** this report is strong on *platform state* (which I verified live, including several findings that invalidate assumptions in the original brief) and deliberately weak on *demand volume*. Where the brief asks "is the audience large enough", the honest answer is: **not measurable with the tools available; a specific follow-up measurement plan is provided in §"What I would investigate next".**

---

# Executive Summary

The idea in the brief is **substantially invalidated as of 2026-09-17**, for reasons that have nothing to do with competition or market size. The evidence points to three separate, severe problems.

**1. The named data sources have largely stopped being bounty catalogs.**

- **OnlyDust is shut down.** Its homepage is now a public post-mortem: *"The OnlyDust chapter closes here."* It distributed **$18M to 4,000 contributors over four years**, then states that **maintainers stopped accepting the money** — *"Low-skill contributors were flooding them with AI-generated code. Maintainers couldn't tell if they were talking to humans or bots."* `[VERIFIED]` — https://onlydust.com/ (retrieved 2026-09-17; `https://onlydust.com/manifesto` serves the same page). The company relaunched as `ctrlg.com` (code-safety/security).
- **Algora has pivoted to recruiting.** Homepage title: *"Algora - Hire the top 1% open source engineers"*; positioning: *"Algora connects companies and engineers for full-time and contract work."* `[VERIFIED]` — https://algora.io/ . `https://algora.io/bounties` returns **HTTP 404** `[VERIFIED]`, `https://docs.algora.io/` redirects to the recruiting homepage `[VERIFIED]`, and the canonical open-source repo `github.com/algora-io/algora` is now described as *"Hire the top 1% OSS engineers"* `[VERIFIED]`. Bounties survive only as an internal recruiting instrument ("trial your candidates using bounties & contracts").
- **Polar no longer does issue funding.** https://polar.sh/ is now *"A billing platform for the intelligence era"* (merchant-of-record billing, usage metering, subscriptions, seats, credits). `https://polar.sh/bounties` → **404**. Its sitemap lists 25 URLs, **none** bounty-related; `docs.polar.sh` redirects to billing docs. `[VERIFIED]`
- **IssueHunt is now a Japanese security bug-bounty platform.** Homepage: *"IssueHunt - #1 Bug Bounty Platform in Japan"*, *"Showcase your security skills."* Its sitemap contains only `/programs`, `/leaderboard` and ~8 security program pages — no OSS-issue bounty catalog. Its terms page is titled *"Issuehunt Vulnerability Disclosure and Bounty Programs"*. `[VERIFIED]`

So of the five sources the brief names as the foundation, **one is dead, three have pivoted away from the use case, and the remaining one (HackerOne/IBB) is a categorically different product** (coordinated security disclosure, not software-development work).

**2. The single most important source has no usable public data feed.** Algora still exposes a public-looking API — `GET https://algora.io/api/trpc/bounty.list` — and it returns **HTTP 200 with an empty list**: `[{"result":{"data":{"json":{"items":[],"next_cursor":null}}}}]`. `[VERIFIED, live call 2026-09-17]` The controller behind it hard-codes `render(conn, :index, bounties: [])` in both clauses and its filtering logic has been **commented out**, while the JSON serializer still fully implements a rich bounty payload. `[VERIFIED]` — `lib/algora_web/controllers/api/bounty_controller.ex` and `.../bounty_json.ex` on `main`. Algora's aggregate bounty listing (`/bounties`, `/bounties/:tech`) sits behind `live_session :authenticated` with `ensure_authenticated` `[VERIFIED — router.ex]`, so an anonymous aggregator cannot even point users at it. Per-organization pages still work (e.g. `https://algora.io/cal/bounties` returns 200 with "1 claim") `[VERIFIED]` — but there is no public index to enumerate them from.

**3. The "unique" product already exists, is priced, and is live.** `https://bountyos.rovidev.com/en/` is titled *"GitHub Bounty Radar | Algora, Opire, IssueHunt Alerts"* and advertises: automatic scanning of Algora, Opire and IssueHunt; a 0–115 scoring model; stack/platform filters; competitor counts; freshness ("fresh 2h"); an "abandoned attempt" signal; **email + Discord alerts**; a pricing page; and a read-only demo. It is self-described as *"Early access · Jul 2026"* `[VERIFIED]`. A second, independent implementation exists on GitHub/npm: `bounty-radar` — *"Find paid open-source bounties on GitHub. Aggregates Algora, label-based, and title-based bounties with competition scoring"* `[VERIFIED]`. There is also a paid commercial scraper on the Apify marketplace (web3/USDC focus) `[VERIFIED]`, plus `bountybureau.com` (*"Verified open-source bounties from GitHub"*) `[VERIFIED]`. The five-way "differentiator" list in the brief (unified search, matching, effort/reward, competition detection, freshness) is already implemented in public by at least one competitor.

**4. The measurable inventory is small, decaying, and polluted — and GitHub's terms constrain commercial re-publication.** `[VERIFIED, GitHub Search API, 2026-09-17]`

| Query | Result |
|---|---|
| `label:bounty is:issue is:open` | **4,396** open issues |
| `label:"💎 Bounty" is:issue is:open` | **556** open issues |
| `label:"💎 Bounty" is:issue` (all states) | **3,923** |
| `label:"💎 Bounty" created:>2026-01-01` | **498** |
| `label:"💎 Bounty" created:>2026-06-01` | **6** |
| `"open source bounties" in:title type:issue` (all time, whole platform) | **17** |
| `"where can I find bounties" in:body type:issue` | **1** (a 2019 Gitcoin design issue) |

The top-ranked result for *both* the `label:bounty` and `label:"💎 Bounty"` queries is **not a real bounty**: `zhangjiayang6835-cyber/bounty-plaza#1575`, titled *"[Bounty] $999999999999999999 BOUNTY FOR IMPLEMENTING THE UNIVERSE INTO OMNIBLOCKS"*, and `SecureBananaLabs/bug-bounty#11398`. The label is shared with spam farms and security-program repos, so raw label counts **overstate** real inventory, while the Algora-specific label appears to have collapsed in new creations since ~June 2026 (6 in ~3.5 months). Independent of that decay, GitHub's Acceptable Use Policies state: *"You will not reproduce, duplicate, copy, sell, resell or exploit any portion of the Service, use of the Service, or access to the Service without our express written permission"*, and the only permitted uses of platform information are **research (open-access publication)** and **archival**, with an explicit ban on using it *"for spamming purposes, including ... sending unsolicited emails to users or selling personal information, such as to recruiters, headhunters, and job boards."* `[VERIFIED]` — GitHub AUP §6, §7. A commercial, monetized, alerting aggregator of GitHub-derived bounty data sits in a gray zone at best, and the alerting/matching use case is close to the explicitly named prohibition.

**5. The structural risk is bigger than the discovery problem.** OnlyDust's own account says the supply side is *withdrawing*: maintainers rejecting external contributions because of AI-generated low-quality submissions. That is a direct threat to a product whose consumer-side value is "more contributors reaching more issues." It also means a bounty aggregator can plausibly *worsen* the ecosystem it monetizes (by routing volume toward the review bottleneck), which is a reputational and ecosystem risk, not just a product-feature risk.

**Bottom line:** The discovery problem may be real, but on 2026-09-17 the *supply* of aggregated paid OSS bounties has contracted so sharply — one dead platform, three pivoted, one category-mismatched, and a measurable single-digit-to-hundreds live inventory — that the product's core value proposition ("one place to search many bounty sources") currently has too little to search. Combined with (a) an already-shipping competitor, (b) a gutted public API on the most important source, and (c) GitHub AUP language that constrains commercial re-publication, **the recommendation is: do not build this as specified.** A narrowed, explicitly non-commercial or clearly-differentiated variant is defensible; the full concept is not. The strongest surviving opportunity identified is described in §17/§19 — and it is *not* a search engine for bounties.

---

# 1. Problem Validation

**Q: Does a real problem exist?** Partially. Developers do report difficulty finding paid OSS work `[SECONDARY]` — the informational layer is real and crowded (see §11). But a *problem* requires both demand and supply; this report finds demand that is plausible-but-unmeasured, and supply that is measurably shrinking.

**Q: Do developers struggle to discover paid bounties across platforms?** The evidence available does not support a strong "yes":
- Developers are not asking about it on GitHub itself: **17** issues in the entire history of GitHub have "open source bounties" in the title; **1** issue ever contains "where can I find bounties" in its body `[VERIFIED, GitHub Search API]`.
- The fragmentation premise is weakened by the fact that the platforms have **stopped fragmenting**: there are fewer independent catalogs to aggregate in 2026 than in 2024.
- Reddit/HN discussions exist in search indexes (e.g. `r/opensource` thread "Algora vs Polar as bounty platforms for…") but **could not be retrieved or verified** from this environment `[COULD NOT CONFIRM]`. One such thread cannot carry a market thesis anyway.

**Q: Are existing platforms fragmented enough for an independent aggregator to add value?** Historically yes; today, materially less. Three of the largest catalogs removed themselves. The surviving fragmentation is mostly *within* GitHub (labels, `/bounty $X` comments, `/reward` comments) rather than *across* platforms — which is a different product (a GitHub-native search/notification layer, not a multi-platform aggregator).

**Q: Are there already products doing exactly this?** **Yes.** §10 documents `BountyOS` (the exact concept, live, with pricing and alerts) and `bounty-radar` (an open-source implementation of the same idea), plus commercial meta-layers (Apify actor, OSS.Fund directory).

**Q: What do competitors do poorly?** From public page content (not hands-on use — `[UNVERIFIED]` where it concerns behavior):
- BountyOS exposes **no verification/methodology page** on its public surface; its scores ("WORK 115", "SNIPER 98") are unexplained magic numbers. That is a trust gap a competitor could exploit — but it is also a gap BountyOS can close in an afternoon.
- `bounty-radar` has a stale repo (created and last pushed 2026-04-02) and a label/title-based approach that inherits the pollution measured in the Executive Summary (it would surface the `bounty-plaza` spam).
- No one visibly solves the **inventory-attrition** problem (dead bounties, withdrawn maintainers) — `bounty-radar`'s "competition scoring" and BountyOS's "abandoned attempt" tag are the only adjacent attempts.

**Q: Is there a realistic differentiation opportunity?** Marginal, and *not* where the brief looks. See §17.

**Q: Standalone product or a feature platforms can copy?** It is a **feature**, and it is being copied by third parties already, not by the platforms. Note the asymmetry: Algora's own repo is **AGPL-3.0 and self-hostable** `[VERIFIED]`, so a self-hosting fork is legally available to anyone — the aggregation layer is the only defensible surface, and it is thin.

**Q: Is the audience large enough?** **Unmeasurable from this environment.** The best available proxy is inventory size, and inventory is small: hundreds (not tens of thousands) of plausibly-live bounty issues.

**Q: Strongest reason to use this instead of going directly to Algora/Polar?** As of the research date, **none of the original reasons survive**: Algora's public catalog is auth-gated and its API returns empty; Polar has no bounties; IssueHunt's bounty product is security-only; OnlyDust is gone.

---

# 2. Bounty Ecosystem

The ecosystem has consolidated/attrited along four distinct axes that the brief conflates:

| Category | What it is | State on 2026-09-17 |
|---|---|---|
| **Issue-bounty tools** (pay per GitHub issue/PR) | Small, tool-like products attached to GitHub | Contracted. Polar exited; Algora demoted bounties to a recruiting feature; OnlyDust dead |
| **OSS-focused security bounty** | Vulnerability disclosure for OSS | Alive and growing (HackerOne/IBB; IssueHunt pivoted *into* this; huntr repositioned to AI/ML security) |
| **Web3 / crypto bounties** | Token-funded OSS tasks, grants | Historically large, now visibly shrinking (OnlyDust dead; Opire unverifiable; multiple dead directories) |
| **Grants / sponsorship** | Recurring funding, not per-task | Alive (Gitcoin "Fund What Matters" `[VERIFIED]`; Open Collective etc.) — but **not** the brief's use case |

**The ecosystem-level event that matters most:** OnlyDust's shutdown note is the only public, first-party, ecosystem-wide diagnosis available, and it says the bottleneck *moved*: from *funding* to *trust in contributed code*. `[VERIFIED]` Any product built on "more paid tasks → more contributors" is swimming against that current.

**Also note:** the ecosystem is now dense with *informational* participants (directories and guides: OSS.Fund, libhunt topic pages, dev.to/Medium listicles, alternativeto entries, `disclose/bug-bounty-platforms`). The "where do I find bounties" question is being answered by content marketing, not by a search product — which means an aggregator's acquisition channel is already owned by cheaper competitors.

---

# 3. Bounty Source Comparison

Fields are filled only where verified. **"Aggregation allowed?" is answered from retrieved legal text or explicitly marked unknown.** "n/a" means the field does not apply.

### Tier A — structured data was reachable or verified-reachable in this session

| Field | Algora | IssueHunt | HackerOne (incl. IBB) |
|---|---|---|---|
| Platform | Algora | IssueHunt | HackerOne |
| URL | https://algora.io/ | https://issuehunt.io/ | https://hackerone.com/ibb |
| Type | OSS bounty + jobs/contracts (now recruiting-led) | Security bug bounty (Japan) | Security bug bounty |
| Active? | **Yes**, but bounties are secondary to recruiting | Yes (as security platform) | Yes |
| Active bounties | 556 open issues carry its label (`💎 Bounty`) — **polluted**, non-Algora repos use it too; 6 created since 2026-06-01 | ~8 public programs visible in sitemap | IBB is one program; scope not statically retrievable |
| API | **Yes but non-functional.** `GET /api/trpc/bounty.list` → 200 with `items: []` (hard-coded) | None found | Yes — participant-scoped ("Pull vulnerability reports / Access your program information / Award a bounty / Import external findings") |
| API docs | `docs.algora.io` → redirects to marketing homepage (no docs) | None found | https://api.hackerone.com/docs/v1 |
| Public data | Per-org pages (`/{org}/bounties`), e.g. `/cal/bounties` → 200; aggregate `/bounties` requires auth | Public program pages + disclosures | Public program pages (JS-rendered) |
| GitHub integration | Yes (GitHub App: "create bounties & reward tips on issues and PRs") | Yes historically | No |
| RSS/Webhooks | A `/api/shields/:org/bounties` badge endpoint exists (returned **400** for the handle I tried) | Not found | Webhook-ish via program notifications, not public |
| Auth required for data | Yes for aggregate listing | No for public program pages | Yes for API |
| Payment | Fiat + Stripe (repo README: "payment processor to handle payouts, compliance & 1099s") | Bank transfer / PayPal (per site FAQ) | HackerOne-managed payouts |
| Geography | Not verified | "Mainly Japanese companies"; page + messaging in English | Global (varies by program) |
| Min bounty | Not verified | Not verified | Not verified |
| Typical range | Site examples reference `$1000`-style bounties | Not verified | Not verified |
| Terms | https://algora.io/legal/terms — **Last updated 08/17/2021** | https://issuehunt.io/terms — now titled "Vulnerability Disclosure and Bounty Programs" | HackerOne program terms |
| Data restrictions | ToS includes a "Use any robot, spider, or other automatic device, process, or…" prohibition `[VERIFIED by keyword scan]` | Not retrieved (JS-only page) | Program-specific disclosure rules |
| Aggregation allowed? | **Unknown / effectively no public feed.** No explicit permission found; robots.txt is *empty* (all rules commented out or absent) | Unknown | **No for bounty opportunities** — see Tier D |
| Notes | Repo is AGPL-3.0, 1,504★, last push 2026-07-18; self-hostable | Sitemap = 8 security programs + leaderboard | Category mismatch with "software development bounties" |

### Tier B — GitHub-integrated / feed-based, not independently verified here

| Field | Opire | Gitpay | bounty-radar (tool) | Gitcoin |
|---|---|---|---|---|
| URL | https://opire.dev/ (**unreachable from this environment**) | https://gitpay.me/ | https://github.com/JuanM94/bounty-radar | https://gitcoin.co/ |
| Type | Issue bounty (`/reward`) | Payment platform for delivered work | Aggregator tool (CLI/npm) | Grants/public goods funding |
| Active? | `[UNVERIFIED]` — reachable per search index (`opire.dev/home`), and BountyOS claims to scan it. Its GitHub org contains only `Opire/.github`, last pushed **2024-12-17** | `[UNVERIFIED]` — site live, title "Gitpay – The payment platform for work delivered" | **Yes** — repo created 2026-04-02, 10★, 6 forks, 5 open issues, no license file | **Yes** — "Gitcoin – Fund What Matters" |
| API | `[UNVERIFIED]` | `[UNVERIFIED]` | Uses GitHub API + npm package | Historically yes |
| Notes | Cited as a live source by BountyOS; could not be confirmed here | JS-rendered; content not extractable | **Direct prior art for the exact use case** | Not a per-task bounty source |

### Tier C — webpage-only (no structured feed found)

`bountymin.com` (*"Open-Source Bug Bounty & Developer Rewards Platform"*) `[VERIFIED live, content JS-rendered]` · `bountybureau.com` (*"Verified open-source bounties from GitHub"*) `[VERIFIED live]` · `bounties.txpipe.io` (Cardano/TxPipe) `[VERIFIED live]` · `bounties.network` (`[UNVERIFIED]` aliveness; long-lived web3 project) · `hackenproof.com` (security, `[VERIFIED live]`) · `huntr.com` (now *"the world's first bug bounty platform for AI/ML"*) `[VERIFIED]` · `superteam.fun` (Solana talent/bounties) `[VERIFIED live]` · assorted personal projects (`DevBounty`, `bountyboard`, `bounty-aggregator`) whose aliveness is `[UNVERIFIED]`.

### Tier D — should NOT be aggregated

| Source | Reason |
|---|---|
| **HackerOne / Internet Bug Bounty** | (1) The API is scoped to *your* programs/reports, not a public catalog of programs. (2) Security disclosure carries embargo, safe-harbor and duplicate-handling semantics that an aggregator cannot honor. (3) Republishing opportunity data invites legal/ethical exposure. **Recommendation: if included at all, link out only, no mirrored fields.** |
| **Bountysource** | Unreachable (`[UNVERIFIED]`); historical reputation damage around payouts makes it a trust liability if it reappears |
| **GitHub itself, for commercial redistribution** | AUP §6 forbids reproducing/exploiting portions of the Service without express written permission; §7 restricts use of platform information to research/archival and bans uses aimed at recruiters/job boards. See §16. |
| **Any source whose robots.txt blocks or whose ToS forbids automated collection** | Must be individually reviewed; several are JS-only SPA apps where "scraping" is the only technical route and therefore the most legally exposed |

---

# 4. Algora Deep Dive

**What the API actually allows (verified by reading the code and calling it):**

- Route: `GET /api/trpc/bounty.list`, plus `OPTIONS /api/trpc/bounty.list`, plus `GET /api/shields/:org_handle/bounties`. `[VERIFIED]` — `lib/algora_web/router.ex`
- Documented parameters in the controller's `@doc`: `status` (open|paid), `org`, `limit`. `[VERIFIED]`
- **Reality:** both `index/2` clauses call `render(conn, :index, bounties: [])`; the entire `to_criteria/parse_params/parse_status` pipeline is **commented out**. Live response: `[{"result":{"data":{"json":{"items":[],"next_cursor":null}}}]}` with HTTP 200. `[VERIFIED]`
- **Authentication:** none needed — which is why it returns an empty list to everyone, including authenticated clients, since the data is never queried.
- **Rate limits:** none published; no public API documentation exists (`docs.algora.io` → marketing homepage).
- **Payload shape (from the serializer, for schema guidance):** `id`, `point_reward`, `reward.amount` (minor units) + `reward.currency`, `reward_formatted`, `reward_tiers[]`, `tech[]`, `status`, `is_external`, `org{id, handle, name, avatar_url, tech[], github_handle, …}`, `task{id, forge:"github", repo_owner, repo_name, number, source.data{html_url, title, body, user{…}}, status, title, url, body, type:"issue", hash}`, `type/kind/reward_type/visibility`, `bids[]`, `autopay_disabled`, `timeouts_disabled`, `manual_assignments`, `created_at`, `updated_at`. Several org fields are stubbed (`stargazers_count: 0`, `members: []`, `description: ""`). `[VERIFIED]`
- **Bounty lifecycle / claim lifecycle / payment lifecycle:** the open-source repo models them (there is a GitHub App, a `claims/:group_id` live view, Stripe callbacks, `/payment/success|canceled`, `/user/transactions`, a leaderboard). `[VERIFIED]` from `router.ex`. **But none of it is exposed as public, queryable state** — status cannot be monitored by a third party, and completed/expired bounty records are not publicly enumerable.
- **Per-org bounty pages do exist and are public** (`/cal/bounties` → 200, text includes "Create new bounties by commenting /bounty $1000", "Open", "1 claim") `[VERIFIED]`. There is, however, **no public directory of organizations** (`algora.io/projects` → 404), so an aggregator cannot enumerate orgs from the site; it would have to discover them out-of-band (e.g. by scanning GitHub for the label and extracting org handles from `algora.io/{org}/bounties` URLs, or by brute-forcing likely handles).
- **Terms / attribution / third-party aggregation:** ToS dated 2021-08-17; keyword scan surfaced the standard "Use any robot, spider, or other automatic device, process, or…" prohibition and no clause granting aggregation rights. `robots.txt` is effectively empty (no `User-agent` directives active) `[VERIFIED]`. **Conclusion: technical access to a usable bounty feed is currently impossible via the API, and legal permission for aggregation is not granted.** Any Algora data collection would have to rely on GitHub-side signals (labels/comments) rather than on Algora itself.

**Practical implication for the architecture:** for Algora, the aggregator would be a *GitHub label scraper*, not an API client — and it cannot verify bounty status, claims, or payout from Algora. That means the "verified 12 minutes ago" and "2 active claims" features in the brief cannot be honestly implemented for the platform the brief treats as the primary source.

---

# 5. Polar Deep Dive

- **API:** Polar has a well-developed public API — for **billing** (products, subscriptions, orders, customers, checkouts, webhooks) — plus SDKs (`polar-js`, `polar-python`, `polar-go`, `polar-php`, `polar-ruby`, `polar-laravel`, `polar-adapters`, `polar-ingestion`). `[VERIFIED]` — `api.github.com/orgs/polarsource/repos`.
- **Bounty/issue-funding data:** **none found.** `polar.sh/bounties` → 404; `polar.sh/sitemap.xml` (25 URLs) contains features for cost-insights, credits, discounts, finance, merchant-of-record, seats, subscriptions, trials, usage-billing — **no** bounties or "issue funding". `docs.polar.sh` → `/docs/introduction`, billing only. `[VERIFIED]`
- **GitHub integration:** still exists, but as a *benefit/entitlement* mechanism ("Automatically grant GitHub repository access to customers") `[VERIFIED from docs]` — i.e. repository access for buyers, not bounty payments for contributors.
- **Funding/reward model, payment system, rate limits, webhooks:** only billing-relevant today `[VERIFIED for billing; N/A for bounties]`.
- **Aggregation possibility:** **Not applicable.** There is no bounty dataset to aggregate. The correct entry for Polar in this project's source list is "**removed — do not build a collector**".
- `[UNVERIFIED]` The precise date/announcement of the issue-funding retirement could not be retrieved (the blog index returned no matching text in static HTML; no search engine was available).

**Also relevant:** Polar's `robots.txt` explicitly *allows* named AI crawlers (OAI-SearchBot, GPTBot, ClaudeBot, PerplexityBot, Google-Extended, Applebot-Extended) while disallowing `/dashboard`, `/auth`, `/verify-email`. `[VERIFIED]` That is a precedent worth citing in a legal/ToS comparison: Polar chose to permit AI-mediated indexing of its public pages.

---

# 6. IssueHunt Deep Dive

- **Current identity:** *"IssueHunt - #1 Bug Bounty Platform in Japan"*; homepage copy is entirely about security vulnerability reporting (Research → Report → Reward; payouts via bank or PayPal; Japan-focused; FAQ says programs are English-capable). `[VERIFIED]` — https://issuehunt.io/
- **API:** none found. `[VERIFIED — nothing surfaced on the site; no docs site]`
- **GitHub integration:** historically the core of the product; the current site's program flow is report-based, not issue-based. `[VERIFIED for current state; historical integration `[UNVERIFIED]` from this environment]`
- **Public bounty data:** the sitemap exposes `signin`, `signup`, `programs`, `leaderboard`, and per-program `/{uuid}` + `/disclosures` + `/hof` + `/activity`. That is roughly **8 programs**, several identified only by UUID. No OSS-issue bounty catalog. `[VERIFIED]` — https://issuehunt.io/sitemap.xml
- **Status / activity level:** active as a company (© 2025 IssueHunt K.K.; sitemap live) `[VERIFIED]`; **not** an active source of paid OSS development tasks.
- **Payment model:** company pays "on triage or once the issue has been fixed"; transfers via bank or PayPal. `[VERIFIED]`
- **Terms:** https://issuehunt.io/terms renders a JS app titled *"Issuehunt Vulnerability Disclosure and Bounty Programs"* `[VERIFIED]` — the content itself could not be extracted `[COULD NOT CONFIRM]`.
- **Aggregation verdict:** Tier B/C for **security programs only**; it should not be listed as an OSS-development bounty source in the product.

---

# 7. OnlyDust Deep Dive

**OnlyDust is not an aggregatable source — it is gone.** `[VERIFIED]` — https://onlydust.com/ (and `/manifesto`, and `www.onlydust.com` all serve the same page).

Verbatim substance from the shutdown note (short excerpts):

> "The OnlyDust chapter closes here. Thank you for an incredible ride."
> "For the last 4 years, we distributed $18M in grants to 4,000 contributors — first through committees, then through an agent allocating $1M monthly."
> "Then maintainers started rejecting our money. They stopped accepting external contributions entirely."
> "Low-skill contributors were flooding them with AI-generated code. Maintainers couldn't tell if they were talking to humans or bots."
> "The bottleneck moved. It's no longer funding. It's security. It's knowing whether code is safe to merge." — Greg & Paco

Reporting fields: API — none (platform shut down). Data accessibility — none. GitHub integration — historically yes `[SECONDARY]`. Ecosystem focus — Web3 (Starknet/Cairo, Rust) `[SECONDARY]`. Reward/payment — grants/stablecoins `[SECONDARY]`. Terms — **moot**. **Suitability for a general-purpose aggregator — zero; exclude entirely.**

**Why this matters beyond one dead source:** it is the strongest piece of evidence in this entire report about *direction of travel*. A $18M-funded program with 4,000 contributors stopped because maintainers withdrew — the same maintainers an aggregator needs to keep publishing bounties. Any MVP that increases contributor volume toward repositories is pushing on a door that is closing.

---

# 8. HackerOne / IBB Deep Dive

- **Public indexing of opportunities:** HackerOne program pages are public but JS-rendered; no static opportunity data was retrievable. `[VERIFIED for the page rendering; `[UNVERIFIED]` for contents]`
- **API availability:** Yes, but **participant-scoped**: the official docs state the API is for "Pull vulnerability reports / Access your program information / Award a bounty / Import external findings". `[VERIFIED]` — https://api.hackerone.com/docs/v1 . There is **no public "list all programs with scopes and reward ranges" catalog endpoint** in that description. `[UNVERIFIED]` specific rate limits and token scopes (docs page is JS-heavy in this environment).
- **Disclosure restrictions:** HackerOne operates coordinated disclosure; programs define scope, severity and payout rules, IBB is a specific collective program. `[VERIFIED at the page level]` — https://hackerone.com/ibb (title: "Internet Bug Bounty - Bug Bounty Program | HackerOne").
- **Program scope:** program-by-program; not centrally enumerable without the API/partner access. `[UNVERIFIED]`
- **Is aggregation appropriate?** **No, not as a mirrored dataset.** Recommended treatment if the product proceeds at all: a separate, clearly-labeled category that **links out** to programs, without caching scopes, reward tables, or violating embargo states. There is real user value in "which OSS projects pay for security reports", but it is a *directory* problem, solved statically.
- **Separate category?** Yes — the semantics (disclosure, safe harbor, triage, duplicates, severity) are incompatible with "claim this issue and get paid" flows. Mixing them in one search index would produce actively misleading results.

---

# 9. GitHub as a Data Source

### 9.1 How bounties are represented on GitHub (measured)

| Mechanism | Example | Reliability as a signal |
|---|---|---|
| Platform label | `💎 Bounty` (Algora-style; also used by unrelated/spam repos) | **Low** — 556 open matches, but top results are `bounty-plaza` spam and a security repo |
| Generic label | `bounty` | **Very low** — 4,396 open matches, heavily polluted |
| Title convention | `[Bounty] $X …`, `bounty` in title | Low; catches junk like *"$999999999999999999 BOUNTY FOR IMPLEMENTING THE UNIVERSE"* |
| Comment command | `/bounty $1000` (Algora), `/reward` (Opire) | Conceptually the best signal (it is the actual payment primitive), but not measurable through the issue-search API without `in:comments` retrieval |
| Self-hosted Algora | The AGPL repo + GitHub App is installable by any org, so the label can appear without Algora.io involvement | Adds ambiguity to any label-based rule |

### 9.2 Do platforms add predictable labels?
Partially. Evidence: `[SECONDARY]` `bounty-radar`'s own description says it aggregates "Algora, label-based, and title-based bounties" — i.e. its author, who works with this data, concluded that labels and titles are the *available* mechanisms, and still needs three strategies to cover one ecosystem. `[VERIFIED — repo description]`

### 9.3 Can the GitHub Search API / GraphQL discover them?
Yes for discovery; **no for trust.** The search API supports label/text qualifiers and returns issue metadata (title, body, labels, state, timestamps, repo) — which is enough to *find candidates* and far from enough to know whether money is real, attached, unpaid, or already claimed. `[VERIFIED — API responses]`

### 9.4 How much useful data can be obtained without scraping?
A great deal — **for discovery**. For any *money* field (amount, currency, claim count, payout state), the amount may exist in text (title/body/comment) and require parsing; everything else must come from the platform, and for Algora the platform provides nothing public.

### 9.5 Rate limits — are they a serious problem?
**Yes, for a crawl-everything design; no, for a targeted design.** Verified figures `[VERIFIED — docs.github.com]`:

- Search API: **30 requests/min authenticated**, **10 requests/min unauthenticated**; code search requires authentication and is limited to **10 requests/min**.
- **Up to 1,000 results per search query** (hard cap).
- Core REST: **60 requests/hour unauthenticated**, **5,000/hour** authenticated; GitHub App installation tokens start at 5,000/hour and scale with users/repos **to 12,500/hour**.
- Secondary limits: ~**900 points/min** for REST, ~80 content-generating requests/min.

Consequences: (a) an unauthenticated cron-based collector is essentially unusable (10 searches/min, 60 core calls/hour); (b) with a GitHub App on a handful of repos, 5,000–12,500 core calls/hour is workable for a curated repository set; (c) the 1,000-result-per-query cap means broad queries must be **partitioned** (e.g. by `created:` windows or by `owner:`) to avoid silently truncating inventory; (d) the labels are polluted, so a large fraction of the quota is spent fetching spam that must be filtered — the same spam you would then have to *not* display, which is an additional product-quality burden.

---

# 10. Existing Competitors

### 10.1 The direct competitors (exact-match concept)

| Product | URL | What it does | Data sources | Filters | GitHub profile matching | AI | Weaknesses (observed) | Status |
|---|---|---|---|---|---|---|---|---|
| **BountyOS** | https://bountyos.rovidev.com/en/ | "GitHub bounty radar" — scanner + 0–115 scoring ("WORK/SNIPER/WATCH"), alerts, dashboard, read-only demo | Algora, Opire, IssueHunt | Stack + platform; score thresholds (≥70 shown) | Not shown publicly | Not claimed; scoring looks heuristic/rule-based | No public methodology for the score; unclear data refresh; Opire's own health is questionable | **Live, early access Jul 2026, has pricing page** |
| **bounty-radar** | https://github.com/JuanM94/bounty-radar · npm `bounty-radar` | CLI/package that finds paid OSS bounties with competition scoring | Algora + label-based + title-based GitHub signals | Via CLI flags | No | No | Stale since 2026-04-02; 10★; no license file; would inherit label pollution | Live repo, small |
| **BountyBureau** | https://bountybureau.com/ | "Verified open-source bounties from GitHub" | GitHub | `[COULD NOT CONFIRM]` (JS-rendered) | `[COULD NOT CONFIRM]` | `[COULD NOT CONFIRM]` | Unverifiable public surface from this environment | Live |
| **Apify "Bounty Aggregator"** | https://apify.com/theaurora/bounty-aggregator | Paid commercial actor: "Web3 USDC Bounty Aggregator for Developers" | Web3 sources | `[COULD NOT CONFIRM]` | No | No | Web3-only; monetized scraping-as-a-service (also a ToS risk model) | Live |
| **bountymin** | https://bountymin.com/ | "Open-Source Bug Bounty & Developer Rewards Platform" | Own listings | `[COULD NOT CONFIRM]` | `[COULD NOT CONFIRM]` | `[COULD NOT CONFIRM]` | More a platform than an aggregator | Live |

### 10.2 Adjacent/meta participants (they own discovery)

| Product | URL | Role |
|---|---|---|
| **OSS.Fund** | https://www.oss.fund/ (+ `/guides/open-source-bounty-platforms/`, `/models/bounties/`) | Curated directory + editorial guides. Categorizes platform types (issue bounty: IssueHunt/Opire/Gitpay; marketplace: Algora; security: HackerOne/HackenProof), tracks a per-platform **status field**, and instructs: *"Do not recommend discontinued platforms as active options."* Guide "Last reviewed: 2026-06-21". Has a "Submit platform" intake. Maintained by Bilgin Ibryam. **This is the SEO/informational incumbent the brief would be competing with for the "where do I find bounties" query** |
| libhunt topic pages, alternativeto (`/software/algora-bounties`), SaaSHub/xranks/similarweb pages, dev.to & Medium listicles | various | Own the long-tail informational queries with zero marginal cost |
| GitHub directories: `disclose/bug-bounty-platforms`, `djadmin/awesome-bug-bounty`, `kunovsky/paid-open-source-projects` | github.com | Community-maintained lists; the "curated list" version of this product |

### 10.3 Assessment
**Do not assume the idea is unique — it is not.** Two independent products (one shipping/priced, one open-source) already do "aggregate Algora + others, score, alert". The brief's five proposed differentiators (unified search, developer matching, effort-to-reward, competition detection, freshness) map onto *existing* competitor features: freshness and competition are already visible in BountyOS's demo UI, and "abandoned attempt" flags go beyond the brief's list.

---

# 11. Developer Demand & Community Evidence

**Evidence FOR demand (informational, not necessarily product demand):**
- Multiple *current* editorial pieces targeted at the query set: "How to find and win open source bounties in 2026" (https://dev.to/timmothybuilder/how-to-find-and-win-open-source-bounties-in-2026-2b4b) `[VERIFIED — retrieved via search index]`; OSS.Fund's "Getting Paid for Open Source Work" and "Open Source Bounty Platforms" guides `[VERIFIED]`; `opensource.guide/getting-paid` `[VERIFIED in index]`; `contributing.md/getting-paid-for-open-source-work/` `[VERIFIED in index]`.
- A `r/opensource` thread exists in search indexes titled "Algora vs Polar as bounty platforms for…" `[VERIFIED as an index entry]` — **content not retrieved** (Reddit blocked here) `[COULD NOT CONFIRM]`.
- `libhunt.com/topic/bounties`, `catchthesignal.com` (GitHub opportunities), `bounties.txpipe.io` exist, implying an audience segment.

**Evidence AGAINST a large unmet discovery problem:**
- The two most on-point GitHub-wide searches return **17** and **1** issues, all-time. Developers file issues on GitHub constantly about tooling gaps they care about; they are not filing this one.
- The *supply* is contracting (OnlyDust dead with a first-party explanation; Polar exited; Algora demoted; IssueHunt repurposed; measurable recent Algora-label creations in the single digits).
- The "problem" is already answered for free by curated lists and guides, which is the cheapest possible competitor.

**Recurring complaints found (qualitative, from retrieved sources):**
- **AI-generated low-quality contributions destroying collaboration** — the OnlyDust note is explicit and is the only first-party, ecosystem-level grievance retrieved `[VERIFIED]`.
- **Review bottleneck, not funding bottleneck** — same source: *"Working alone was faster. Less coordination overhead."* `[VERIFIED]`
- **[NOT RETRIEVED]** payment concerns, trust issues, stale bounties, duplicate listings, unclear reward conditions, competition. These are asserted in the brief; this environment could not retrieve Reddit/HN to check them. **Do not treat them as validated.**

---

# 12. Data Collection Feasibility

| Source | Best available collection method | Feasibility | Honest confidence in freshness/status |
|---|---|---|---|
| Algora | GitHub App label/comment scanning + per-org page fetch (`/{org}/bounties`) | **Medium** — cannot enumerate orgs, cannot read status/claims from anywhere public | **Low.** "Verified N minutes ago" is not achievable from Algora's side; only "issue still open on GitHub" is |
| Polar | none | **N/A** | — |
| IssueHunt | none (security programs only) | **N/A** for dev bounties | — |
| OnlyDust | none | **N/A** | — |
| HackerOne/IBB | API (participant-scoped) or program pages | **Low** for catalog use | Program pages change rarely; disclosure state must never be mirrored |
| GitHub labels | Search API with partitioned queries | **High technically** | Medium: open/closed is reliable; *money* fields are text parsing only |
| GitHub comment commands (`/bounty`, `/reward`) | Search with `in:comments`; requires fetching comments | Medium; quota-hungry | Cannot confirm payment |
| Opire | `[UNVERIFIED]` — likely API/pages, unreachable here | Unknown | Unknown |
| Gitpay / BountyMin / BountyBureau / TxPipe / Superteam | Page fetch or manual | Low–Medium | Varies; several are JS-only SPAs |
| Web3 grant platforms (Gitcoin) | Public APIs historically | Medium | Different model (grants, not claimable tasks) |

**Feasibility verdict:** a multi-platform aggregator is *technically* buildable, but the honest ceiling today is **"we index GitHub issues that look like bounties, and we link to platforms"** — not "we normalize bounty inventory across platforms with status and competition". Two of the three pillars of the pitch (normalized status, competition counts) are unavailable for the flagship source.

---

# 13. GitHub Developer Skill Analysis

Separating inference classes explicitly, per the brief.

### 13.1 Technically possible from public data only (no user consent needed)
- **Languages**: `/repos/{owner}/{repo}/languages` per repo, aggregated → a defensible "language distribution".
- **Contribution frequency**: public events/commits timestamps → activity cadence (with the caveat that GitHub's public event feed is a limited window).
- **Repo type**: topics, description, stars, forks, size, license, archived-flag, primary language.
- **Issue/PR experience**: counts and timestamps of authored issues/PRs; whether PRs were **merged** (`/repos/{o}/{r}/pulls/{n}.merged`, `merged_at`).
- **Organizational affiliation signal**: org membership where public.

### 13.2 Technically possible, requires user consent + scope
- **Code review experience**: review submissions/comments on others' PRs is much easier to enumerate **as the authenticated user** (and per-repo endpoints require matching permissions on repos you can see).
- **Private-repo activity**: requires `repo` scope — **do not request.** Discouraged.
- **Reliable "merged PR count across all of GitHub"**: expensive and incomplete (search caps at 1,000 results; per-repo enumeration is quota-bound). Better: compute over a **bounded, declared set** of repositories and label it as such.

### 13.3 Unreliable inference (do not present as fact)
- **"Framework expertise"** from language stats alone (a TypeScript repo does not imply React experience).
- **"Seniority"** from contribution counts — trivially gameable.
- **"Skill level"** from repo stars — that measures the repo, not the person.
- **"Can complete this bounty"** — see §14.
- **Recency-weighted skill**: a user with 2019 activity in Rust and 2026 activity in Go is not a Rust expert today; weighting is a modeling choice and must be disclosed.

### 13.4 Data that should NOT be inferred/stored at all
- Email addresses, real names, employers, location — not needed for matching; storing them raises GDPR/privacy obligations for no product benefit.
- Anything derived from private repositories without explicit, revocable consent.
- **Sensitive inferences** (e.g. "this contributor appears to be a bot / low-skill") about *individuals* — OnlyDust's note shows exactly how toxic that framing became in this ecosystem. A "ability score" attached to a developer's identity is a reputational hazard. Prefer **self-asserted skills** + explicit "evidence links".

### 13.5 Minimum-permission approach
Use **GitHub OAuth with no scopes beyond `read:user`** (public profile) plus, optionally, `public_repo` if the user wants the app to read private-org-free PR history they authored in public repos. Everything in §13.1 can be built from public data + the user's login identity. **Do not request `repo`**, and state this visibly — with Algora, Gitcoin, and Polar all having *pivoted toward* trust/safety/OSSO-signals, excessive scopes are a competitive liability.

---

# 14. AI Matching Feasibility

**1. Can it realistically work?** Partially, and the honest part is narrow. The LLM can do two things well: (a) **extract structured requirements from an issue** (skills implied, likely touched areas, explicit acceptance criteria, ambiguity), and (b) **summarize why** a given issue matches a stated skill list. It cannot know whether the developer can complete the task.

**2. Which parts should be deterministic?**
- Language/ecosystem overlap between bounty requirements and the developer's declared/derived skills.
- Repository-level signals: stars, fork count, size, rule-files (`CONTRIBUTING.md`, `CODEOWNERS`), test-presence (`tests/`, CI config), presence of `good first issue`/`help wanted` labels, maintainer responsiveness (median first-response latency on recent issues), and issue age.
- **Competition proxy**: number of distinct non-author users with linked/merge-candidate PRs referencing the issue; claim comments if detected.
- **Staleness**: `updated_at` age of the issue and of the last maintainer comment.

**3. Which parts should use AI?** Requirement extraction, ambiguity detection ("the issue never states expected behavior"), risk flags ("this touches authentication", "no tests exist", "the last 3 issues in this repo were closed without review").

**4. Which parts should use embeddings?** Semantic similarity between (issue text + repo README/topics) and (developer's declared interests + their *past merged PR titles/areas*). This is the right tool for "does this person work in this neighborhood" — and it must be presented as similarity, never as competence.

**5. Which parts require repository/code analysis?** Any claim about touched files, blast radius, or test requirements. Doing this properly means cloning/AST-analyzing the repo — expensive, and (importantly) it is the part most likely to be wrong in an AI-generated estimate.

**6. What could be misleading?**
- A single "87% match" number implies a probability of success. It is not one.
- Effort estimates from issue text alone systematically underestimate (unknown maintainer expectations, missing tests, slow review).
- Extraction can invent a "required skill" that the issue never stated.

**7. How to minimize hallucination?**
- Make every claim **cite a span** of the issue/README (show the quote next to the claim).
- Never emit an amount, status, or claim count from the LLM — those come only from parsed platform/GitHub fields, and if unavailable, show "unknown".
- Use enum-constrained outputs for difficulty/effort buckets; no free-form probability.
- Show a **confidence/missing-information** field, and prefer "insufficient information" to a guess.
- **Labelling requirement (non-negotiable):** every estimate must be labeled "AI estimate — not a guarantee" in the UI, and the product must never imply that a match means the developer will be paid or will succeed. Given the OnlyDust history, overstating AI capability here is not just a UX flaw — it is the mechanism that produced the ecosystem backlash.

---

# 15. Difficulty & Effort Estimation

### 15.1 Usable signals (ranked by my confidence)

| Signal | Source | Trust level |
|---|---|---|
| Explicit acceptance criteria / steps in the issue | issue body | **High** (it is the requirements contract) |
| Existing tests + CI for the touched area | repo files | **High** |
| Files touched by the eventually-merged PR (historically, per repo/area) | merged PRs | **High for similar past tasks; useless for a novel one** |
| Repo size / module count | repo metadata | Medium |
| Issue body length, presence of reproduction steps, screenshots | issue body | Medium |
| Labels (`good first issue`, `help wanted`) | issue | Medium (maintainer-curated, therefore decent) |
| Comment count / age / maintainer responsiveness | issue + repo | Medium (good *risk* signal, weak *effort* signal) |
| Language/framework familiarity of the *reader* | developer profile | Doesn't affect objective difficulty; affects *personalized* effort only |
| "How hard does it look" from an LLM | — | **Low** — label as AI estimate |

### 15.2 What should be shown, and how

- **Difficulty:** `Beginner | Easy | Intermediate | Advanced | Expert`, from a deterministic rule mix (label presence, repo size, area criticality, test coverage) **plus** an AI judgment shown as a *secondary* opinion with an explanation.
- **Effort:** bands `<1h | 1–3h | 3–8h | 8–20h | 20+h` — always displayed as a **range**, with the phrase "AI estimate" and the top 2 contributing signals.
- **Never** display a single point estimate, and never display effort for issues whose requirements could not be extracted (show "needs triage" instead).
- Trust rule: estimates derived from **historical merged PRs in the same repository area** are the only ones worth calling "data-driven"; everything else is a heuristic and must be labeled so.

---

# 16. Legal / Terms / Data Risks

**This section is deliberately non-conclusive. It identifies issues, not legal answers.**

### 16.1 GitHub (the main data substrate) — the highest-risk area
- **AUP §6 Services Usage Limits:** *"You will not reproduce, duplicate, copy, sell, resell or exploit any portion of the Service, use of the Service, or access to the Service without our express written permission."* `[VERIFIED]` — a monetized aggregator that mirrors GitHub-derived listings is in the blast radius of this sentence.
- **AUP §7 Information Usage Restrictions:** permitted uses of platform information are limited to **research with open-access publications** and **archival**. Scraping ≠ API. And: *"You may not use information from the Service … for spamming purposes, including for the purposes of sending unsolicited emails to users or selling personal information, such as to recruiters, headhunters, and job boards."* `[VERIFIED]` — **email alerting about paid work to developers, and any recruiter/marketplace framing, must be reviewed against this.**
- **AUP §4:** prohibits content/activity *"incentivized by (or incentivizes inauthentic engagement with) rewards such as cryptocurrency airdrops, tokens, credits, gifts or other give-aways"* `[VERIFIED]` — relevant if web3 bounties are aggregated and promoted.
- **API terms** live in ToS §H (referenced from the AUP). Not retrieved in full in this session `[COULD NOT CONFIRM]` — **must be read before building any collector.**
- **Rate limits** are contractual-adjacent operational constraints; secondary limits can be applied *"for undisclosed reasons"* `[VERIFIED from docs]` — meaning access can be throttled without a stated cause.
- **Copyright:** issue text and repo metadata are user-generated content; license of the *repository* does not automatically license republishing nor the issue thread verbatim beyond fair-quote/deep-link. **Store minimum necessary, link out, quote briefly.**
- **Privacy:** GitHub profile data is personal data under GDPR for EU users. Only-purpose limitation, storage minimization, deletion-on-request and a stated lawful basis are needed even for "public" data.

### 16.2 Per-source
- **Algora:** ToS dated 2021-08-17 contains an automated-access prohibition ("Use any robot, spider, or other automatic device, process, or…") `[VERIFIED by keyword scan]`; no clause grants aggregation/attribution rights; `robots.txt` is empty/non-restrictive `[VERIFIED]`. **`robots.txt` emptiness is not permission.** ⚠ Legal review required.
- **Polar:** no bounty data → not applicable. Their explicit AI-crawler allowances are a useful precedent, not a licence for other sites.
- **IssueHunt:** terms page not extractable `[COULD NOT CONFIRM]`; program data is security-related and disclosure-sensitive.
- **HackerOne/IBB:** disclosure regimes, safe-harbor language and program-specific rules; mirroring opportunity/scope data is inappropriate. ⚠ Legal review required if included.
- **OnlyDust:** shut down; `ctrlg.com` is a different product. **Nothing to collect.**
- **Opire / Boss.dev / BountySource:** status unknown from this environment; cannot assess terms. ⚠ Must be re-checked before any integration.

### 16.3 Data the product would store about *users* (consent matrix)
| Data | Basis | Consent |
|---|---|---|
| GitHub OAuth identity + public profile | legitimate interest / contract | Consent screen, minimal scopes |
| Derived skill profile (languages, activity) | consent | Explicit, shown to user, editable, deletable |
| Declared skills/interests | contract | User-entered |
| Alert preferences (channels, filters) | contract | User-entered |
| Emails for alerts | consent | Explicit; and see AUP §7's anti-unsolicited-email language |
| Anything from private repos | **Do not collect** | n/a |

### 16.4 Where professional legal review is appropriate (explicit list)
1. GitHub AUP §6/§7 + ToS §H applicability to a *commercial, monetized* index of GitHub-derived bounty data.
2. Whether email/Discord alerting on GitHub-derived data constitutes the prohibited "unsolicited" pattern.
3. Each aggregated platform's ToS (especially Algora's 2021 automated-access clause).
4. Whether security-bounty data (HackerOne/IBB) can be listed at all, and in what form.
5. Data-protection posture for EU developer profiles (lawful basis, retention, deletion, DPIA need).
6. Trademark/attribution obligations for platform names and logos (`/api/shields/*`-style badge usage included).

---

# 17. Technical Architecture Proposal

**Framing first:** the pipeline in the brief assumes platform APIs. **Those do not exist in the assumed form.** The realistic v1 collector set is: (a) GitHub label/comment search, (b) GitHub GraphQL for repository and PR metadata, (c) a *small* number of stable page parsers where ToS/robots permits, (d) manual/curated entries. Design accordingly, and treat every "platform" as a plugin with an explicit `capability` declaration.

```
Source registry (declarative: id, kind, terms_url, robots, capability flags)
        │
        ├── GitHubLabelCollector      (Search API, partitioned queries)
        ├── GitHubCommentCollector    (/bounty, /reward in comments)
        ├── GitHubRepoEnricher        (GraphQL: repo, PRs, maintainer latency)
        ├── HtmlCollector plugins     (only where robots.txt + ToS permit)
        └── ManualCuratedSource       (editorially maintained list)
        │
   RawStore (append-only, source payload + fetch_time + etag)
        │
   Normalizer (→ canonical Bounty + Repository records; every money field nullable)
        │
   Deduplicator (same task across sources)
        │
   Validator / Trust Engine (open? real amount? maintainer active? withdrawn?)
        │
   StatusReconciler (scheduled re-check; decays → "stale", then "unlisted")
        │
   Postgres (source of truth) ──► Search index (Postgres FTS first; OpenSearch only if needed)
        │
   Recommendation (deterministic filters → embeddings → LLM explanation)
        │
   Frontend + Alerts (email/Telegram/Discord; rate-limited, opt-in, consent-tracked)
```

**Which data to store:** bounty identity (source, source id, URLs), repository identity, money (nullable, with `amount_source = "parsed_from_title" | "api" | "unknown"`), status with `status_confidence`, timestamps, raw payload hash, and the *evidence span* for every parsed field.

**Which fields to normalize:** `currency` (ISO-4217 + `CRYPTO:<symbol>`), `status` (`open|claimed|in_review|paid|closed_unpaid|expired|unknown`), `technologies[]` (normalized tags, not free text), `effort_band`, `difficulty_band`, `source`, `repository` (`owner/name`), `platform_url`, `issue_url`.

**Duplicate detection:** exact match on `issue_url`/`(repo_owner, repo_name, issue_number)`; then fuzzy title similarity + same repo + overlapping date window + same amount → "likely duplicate" (surface once, list sources beneath, never merge silently).

**Status updates:** webhook/poll for repos you cover (GitHub webhooks for issues/PRs are free and precise); scheduled re-fetch for everything else with exponential backoff by observed churn; on PR merged referencing the issue → `in_review`→`paid`/`closed_unpaid` transition with **confidence**, never asserted.

**Expired/stale detection:** decay rules — `stale` if no activity for N days *and* issue open; `probably_unclaimed` if no linked PR and no claim comment; `withdrawn` if maintainer comment matches withdrawal patterns *or the repo has gone contribution-gated* (see below). Show the rule name in the UI so users can trust it.

**Bounty changes:** treat each observation as an immutable snapshot; show "changed: amount $300 → $150 (2 days ago)" rather than overwriting silently.

**Deleted issues / closed PRs:** soft-delete locally, mark `gone`, keep the historical row for user alert history integrity, and stop displaying it in search.

**Detecting "already claimed":** the only honest signals are (a) claim comments/bot comments, (b) linked PRs from non-author users, (c) assignment. All three are *proxies*. Label the UI accordingly ("2 PRs reference this issue").

**Avoiding stale opportunities (the hard one, and the real product value):** add a **repo-level contribution gate** signal — does the repo accept external PRs at all? Checking `pull_request_creation_policy`, `CONTRIBUTING.md` recent changes, and the merge rate of recent external PRs detects the exact pattern OnlyDust described (maintainers closing the door). A bounty board that surfaces "this project stopped accepting outside contributions" is genuinely useful and nobody is doing it. **This is the strongest surviving differentiator.**

**Explicitly do NOT build:** a scraped mirror of Algora/Polar data; a security-bounty index that stores scopes; anything requiring `repo` OAuth scope.

---

# 18. Database Proposal

Refinements to the brief's schema are marked **NEW** or **CHANGED**. Everything money- or status-related is nullable with provenance.

```sql
-- Source registry (drives capability-aware UI; prevents lying in the interface)
source (
  id, slug, name, homepage_url, terms_url, robots_url,
  kind,                       -- github_label | github_comment | platform_api | html | manual
  has_api, api_docs_url,
  aggregation_permitted,      -- allowed | unclear | prohibited | unknown
  legal_review_state,         -- not_reviewed | reviewed_ok | reviewed_restricted | do_not_use
  capability jsonb,           -- {money:true,status:false,claims:false,competition:false}
  enabled bool, notes, created_at, updated_at
)

repository (
  id, gh_id, owner, name, url, stars, forks, open_issues_count,
  primary_language, topics text[], license, archived bool, size_kb,
  accepts_external_pr bool,            -- NEW: contribution gate
  pr_creation_policy text,             -- NEW
  external_pr_merge_rate_90d numeric,  -- NEW
  maintainer_first_response_median_hours int,  -- NEW
  has_ci bool, has_tests bool, last_synced_at
)

bounty (
  id, source_id, source_bounty_id, canonical_key,   -- canonical_key: issue url hash
  title, description,
  url, platform_url, issue_url,
  repository_id, ticket_number,
  amount_minor bigint NULL, currency char(3) NULL,
  amount_max_minor bigint NULL,                     -- NEW: ranges ($100–$300)
  amount_source text,                               -- NEW: api|parsed_title|parsed_comment|unknown
  amount_evidence text,                             -- NEW: the span that produced the amount
  reward_type,                                      -- cash|crypto|points|unknown
  status text, status_confidence numeric,           -- NEW
  status_rule text,                                 -- NEW: which rule decided it
  difficulty_band text NULL, difficulty_confidence numeric NULL, difficulty_is_ai bool,
  effort_band text NULL, effort_confidence numeric NULL, effort_is_ai bool,
  claims_seen int,  pr_refs_seen int,                -- NEW: honest competition proxies
  first_seen_at, last_seen_at, last_verified_at,
  created_at_source, updated_at_source,
  expires_at, claimed_at, paid_at,
  gone bool,                                         -- NEW: issue deleted/closed upstream
  raw_payload_hash, created_at, updated_at
)

bounty_technology (bounty_id, tag_id)             -- normalized tags, not free text
bounty_observation (                               -- NEW: append-only snapshot log
  id, bounty_id, observed_at, payload jsonb, diff jsonb
)

developer (
  id, gh_id, login, avatar_url, oauth_scopes text[],
  skill_profile_consent bool, consent_at, updated_at
)
developer_skill (
  developer_id, tag_id, weight numeric,
  evidence_kind text,        -- declared | derived_language | derived_pr_title | derived_repo_topic
  evidence_url text,
  recency_days int, is_self_asserted bool
)

match (
  id, developer_id, bounty_id, generated_at,
  deterministic_score numeric, semantic_score numeric,
  score numeric,
  reasons jsonb,             -- [{claim, evidence_span, source_url}]
  missing_skills text[], risks text[],
  model, prompt_version, is_ai_estimate bool     -- NEW: provenance for every AI claim
)

alert_subscription (
  id, developer_id, channel,               -- email|telegram|discord|rss
  filters jsonb, min_score numeric, cadence, created_at, disabled_at,
  consent_basis, consent_at
)
impossible_source_log (                      -- NEW: auditable record of "we cannot know this"
  id, source_id, wanted_field, reason, first_recorded_at, last_checked_at
)
```

**Where I disagree with the brief's schema:** (1) `amount` as a single non-null number invites fabricated values — split into `amount_minor`/`amount_max_minor` with `amount_source` and `amount_evidence`; (2) `status` without `status_confidence`/`status_rule` will silently lie about claims and payouts; (3) `difficulty`/`estimated_effort` need `*_is_ai` flags or the UI cannot label them honestly; (4) the brief's `Match.reasons` should carry **evidence spans**, not free text, or it becomes unverifiable AI narration; (5) there is no table for *source capability* — without it the product cannot tell the truth per-source; (6) add the repository contribution-gate fields (they power the one differentiator nobody else has).

---

# 19. MVP Proposal

Given §2–§10, the MVP must change shape. Two options are presented; the second is the one I would ship.

### Option A — the brief's MVP, narrowed (defensible but weak)
**MVP v1 (2–4 weeks):** 1 source only (**GitHub**), keyword/label ingestion for a **curated allow-list of repositories** (not all of GitHub), canonical bounty records with hard-nullable money fields, search + filters (language, repo, amount range, status, age, platform), bounty detail with attribution and deep links, "verified N hours ago" based on GitHub's `updated_at` only, stale/unlisted decay, explicit "we could not verify" labels.
**MVP v1.5:** GitHub OAuth (no `repo` scope), self-declared + derived-from-public-data skill profile, deterministic match filters, saved searches.
**v2:** LLM requirement extraction, embeddings, alerts, and *only then* additional sources — each one gated by legal review and a capability declaration.

*Why this ordering:* v1 buys you truthful data about one source before you build normalization abstractions for sources that may not exist. v1.5's matching must be deterministic-first so that v2's AI has something honest to explain.

### Option B — the differentiated MVP (recommended, see §17 and §25)
**Ship the "contribution viability + effort-to-reward" product, not the "bounty search engine".**
**v1:** For a curated repo allow-list: index bounty-ish issues; compute **viability** (is this repo still accepting external PRs? how fast does the maintainer respond? are there tests? was the last external PR merged?) and **effort-to-reward** bands with labeled AI estimates; deep-link to the platform for everything you cannot verify. Zero mirroring of platform data you have no license for.
**v1.5:** personal matching within that allow-list (declared skills + public GitHub evidence), RSS/email alerts only after the AUP §7 review.
**v2:** multi-source *only* for sources that pass legal review with a real API; security category kept strictly separate and link-only.

**What does NOT belong in any MVP:** HackerOne/IBB mirroring; Algora API integration (it returns empty); "2 active claims" as a hard number; anything requiring `repo` scope; any scraping of JS-only sites without a terms review.

---

# 20. Future Roadmap

| Phase | Content | Gate to proceed |
|---|---|---|
| 0 (now) | Re-verify sources; measure real inventory with the plan in the final section | ≥200 genuinely-live, verifiable listings across ≥2 sources |
| 1 | Option B v1: viability + effort-to-reward on a curated repo allow-list | Users report the viability signal is trustworthy in ≥3 repos |
| 1.5 | GitHub login, skill profile, deterministic matching | D30 retention > 15% among activated users |
| 2 | LLM extraction (with evidence spans) + embeddings, alerts (post-legal review) | Drop in "wrong amount/status" reports < 2% |
| 3 | Additional sources via a plugin SDK, each with a capability declaration and a legal-review record | A source that passes both technical and legal review |
| 4 | Open datasets: publish the normalized schema + a non-redistributable-licensed derived dataset (careful: AUP) | Legal sign-off |
| 5 | Notifications ecosystem (Telegram/Discord), analytics, "maintainer dashboards" (the side that actually pays: *maintainers* want to know what to fund and who is safe to accept from) | Willingness-to-pay evidence from maintainers |

**Roadmap note:** the only phase with a plausible commercial future is **phase 5 (maintainer-side tooling)** — maintainers have budget (companies) and a real problem (OnlyDust's security/trust bottleneck). Developers seeking bounties are notoriously hard to monetize and are the population that already has free alternatives.

---

# 21. Monetization Possibilities

| Model | Compatibility | Evidence-based assessment |
|---|---|---|
| Free + Pro (developers pay for alerts/filters) | Low | The brief's own target users are hunting money; BountyOS is already in early access with a pricing page `[VERIFIED]`, and OSS.Fund gives the informational layer away free. Price pressure is downward from day one |
| Paid alerts | Low–Medium | Telegram/Discord alerts are trivially self-hostable (a bot + GitHub webhooks, ~50 lines) |
| Maintainer/company promotion, sponsored listings | **Medium** | Mirrors Algora's own pivot (they monetize the *hiring* side). A promoted bounty is only trustworthy if you never mix it with organic ranking without a label |
| API access as a product | **Low** | Only if you own a dataset others cannot get — and here the data is openly available and legally constrained to republish |
| Maintainer dashboards / B2B tooling (post bounties, screen contributors, detect AI-slop PRs) | **Highest** | This is where the ecosystem's money and pain both are (OnlyDust's "bottleneck moved" thesis). Also the direction Algora, Polar and ctrlg all independently moved toward |
| Security-category sponsorships | Medium | Attractive but drags in HackerOne-style compliance |
| **Beware:** any model that begins to look like a recruiter/job-board product is close to GitHub AUP §7's prohibited uses | — | Literally named: "recruiters, headhunters, and job boards" |

**Trust-damaging models to avoid:** paid ranking of bounties without disclosure, charging developers to see opportunities, selling developer profiles or contact data, "unlock premium bounties" gating.

---

# 22. Open Source Strategy

**Recommendation: open the collectors and the schema; keep nothing secret that would damage trust, and expect no moat from any of it.**

- **Collectors: open source.** They are ~30% of the work, no one's moat, and open collectors are the fastest route to community-maintained source plugins (which solves §3's long tail). Also: legitimacy. If the collectors are public, the ecosystem can audit that you are not a spam engine.
- **Database schema: open** (per §18). Machine-readable export of the *schema* is free; the *data* is where license and AUP questions live (see below).
- **Frontend: open source.** Cheap, and it makes the "how do you compute viability/effort" logic auditable — which is the trust argument against BountyOS's opaque 0–115 scoring.
- **Recommendation engine: open by default; keep prompts/models as configuration, not secrets.** There is no defensible proprietary algorithm here; the honest differentiator is *methodology transparency* plus data hygiene.
- **Data redistribution: do NOT blanket-open.** A bulk mirror of GitHub-derived personal-adjacent data collides with AUP §6/§7 and GDPR. If you publish anything, publish aggregates (counts, distributions) and keep listings as deep links.
- **Users contributing new sources:** yes — via a plugin interface + a mandatory `capability` and `legal_review_state` field in the PR template. This is how an open project scales the source list while keeping the legal record.
- **What an open-core model would have to protect:** nothing convincing. If the product ever becomes maintainer-side B2B tooling (§21), that is where closed components would legitimately live.

---

# 23. Main Risks

| # | Risk | Severity | Evidence |
|---|---|---|---|
| 1 | **Source collapse** — the inventory the product indexes is shrinking | **Critical** | OnlyDust dead; Polar exited bounties; Algora demoted bounties to recruiting; IssueHunt repurposed `[VERIFIED]` |
| 2 | **No usable public API for the flagship source** | **Critical** | Algora `bounty.list` returns `[]`; aggregate listing is auth-gated; no docs site `[VERIFIED]` |
| 3 | **GitHub AUP §6/§7 restrict commercial re-publication and recruiter-like use** | **High** | Verbatim clauses retrieved `[VERIFIED]` |
| 4 | **Label pollution makes the primary discovery mechanism noisy** | **High** | 4,396 open `label:bounty`; top hits are `bounty-plaza` spam and a security repo; 6 new Algora-label issues since 2026-06-01 `[VERIFIED]` |
| 5 | **Already-shipping competitors cover the concept** | **High** | BountyOS (priced, alerting) + bounty-radar + Apify actor + BountyBureau `[VERIFIED]` |
| 6 | **Marketplace-vs-feature** — the aggregation layer is thin and could be added by any of the remaining platforms | Medium | Algora's own roadmap already moved to screening/matching |
| 7 | **Ecosystem backlash risk** — a tool that routes more contributors into repositories amplifies the exact dynamic maintainers rebelled against | **High** | OnlyDust's note, quoted verbatim `[VERIFIED]` |
| 8 | **Maintenance burden vs. decaying supply** — reconciliation against sources that expose no status means the honest UI is mostly "unknown" | High | §12, §17 |
| 9 | **Demand unproven** | **High** | 17/1 GitHub issues; no volume data available; Reddit/HN unretrievable |
| 10 | **Rate-limit/policy fragility** — 60/hr unauthenticated, 10 searches/min, 1,000-result cap, secondary limits applied without notice | Medium | GitHub docs `[VERIFIED]` |
| 11 | **Privacy/GDPR exposure** for developer profiles | Medium | §16 |
| 12 | **Legal cost** of reviewing every source's ToS (and re-reviewing as they change) | Medium | §16.4 list |

---

# 24. Unresolved Questions

1. How many **genuinely live, claimable, paying** OSS bounties exist today, deduplicated across all platforms? (Measured proxies: 556 open with Algora's label, polluted; not deduplicated, not verified as funded.)
2. Is Opire alive and does it have an API? `[UNVERIFIED — unreachable from this environment]`
3. What are Boss.dev's and BountySource's current status? `[UNVERIFIED]`
4. Did Algora publicly announce deprioritizing bounties, and what does its current ToS say about third-party indexing? (ToS retrieved is **from 2021** — likely stale relative to the current product.)
5. What does GitHub ToS §H (API Terms) say about derivative/commercial indexes? `[COULD NOT CONFIRM]`
6. Exact IssueHunt terms for its current security program product `[COULD NOT CONFIRM]`.
7. Do developers actually want this? (Requires Reddit/HN/Google Trends access, unavailable here.)
8. How large is the "maintainer willingness to fund external work" pool in 2026, post-OnlyDust? (This determines whether phase 5 has a market.)
9. Do BountyBureau / BountyOS have real users? (No public traction signals retrieved.)
10. Are the alert channels (email/Discord) AUP-compliant for GitHub-derived data? (Legal question, not a research question.)

---

# 25. Evidence-Based Conclusion

**The concept, as specified, should not be built.** This is not a hedge — it follows from live-verified facts:

1. **Supply is gone or repurposed.** OnlyDust (shut down, with a first-party explanation), Polar (no bounties), IssueHunt (security-only), Algora (recruiting-first, auth-gated catalog, empty public API). The "aggregate many platforms" premise has fewer platforms today than when the idea was conceived, and the two most-cited ones are no longer bounty catalogs.
2. **The flagship source cannot be integrated honestly.** An empty API plus an auth-gated listing means features like "verified 12 minutes ago" and "2 active claims" would be fabricated for Algora. A product whose promise is verified freshness cannot be honest about its main source.
3. **The differentiators already exist in public.** BountyOS ships unified search + scoring + competition + freshness + alerts with a pricing page; bounty-radar ships the same concept open-source.
4. **The measurable market is small and noisy.** Hundreds (not thousands) of plausible listings, diluted by spam where the label-based discovery method is used, and a recent-creation count in the single digits for the one platform-specific label I could measure.
5. **The commercial/legal ground is constrained.** GitHub AUP §6/§7 restrict reproducing and commercially exploiting Service information, and explicitly name recruiters/headhunters/job boards — the adjacency this product drifts toward.
6. **The ecosystem's own diagnosis points elsewhere.** The bottleneck is trust/security, not funding. A tool that routes more (increasingly AI-generated) contributions into repositories is working against the current that killed OnlyDust.

**What *is* worth building (the survivor):** a **contribution-viability layer** — for a curated repository allow-list, tell a developer not just "here is a paid issue" but "this project still accepts external PRs, the maintainer responds in ~2 days, there are tests, the last external PR was merged, and this task is a 3–8 hour job at $150" — with labeled AI estimates, evidence spans, deep links, and zero unlicensed data mirroring. That product is honest about what it cannot know, is not covered by any competitor I found, and its maintainer-side sibling (post bounties, screen contributors, detect low-quality/AI-generated PRs) is where the ecosystem's money actually is. Note also that this pivot moves the product *toward* the same destination Algora, Polar and ctrlg independently chose — which is simultaneously evidence that the destination is real and a warning that it will be crowded by better-funded players.

---

# Final Decision Framework

### Problem
**Weak / unvalidated.** A discovery complaint plausibly exists in the developer community, but direct measurement failed: GitHub-wide interest is 17 and 1 issues all-time, and Reddit/HN/Google Trends were unavailable. **Uncertainty: high.** What *is* certain is that the platforms have stopped supplying the fragmented catalogs the problem statement assumes.

### Data
**Insufficient today, and legally constrained.** Verified: Algora's public API returns empty; Algora's aggregate listing is auth-gated; Polar/IssueHunt/OnlyDust supply nothing; HackerOne is category-mismatched and disclosure-sensitive; GitHub labels are usable for discovery but noisy (4,396 raw → unknown true count) and constrained by AUP §6/§7. **Verdict: no.**

### Technology
**Yes** — a small developer/team can absolutely build this (collectors + Postgres + FTS + a UI is weeks of work, and `bounty-radar` proves the ingestion concept). **But technical feasibility is not the binding constraint**; the binding constraints are data availability and terms. **Verdict: yes technically, blocked in practice.**

### Differentiation
**Currently none in the specified feature list** — every listed differentiator is implemented by at least one live competitor. The only found differentiator that is *not* covered is **contribution viability** (does this repo still accept external contributions, and how quickly does review happen) plus **trust through transparent methodology** versus BountyOS's opaque scoring. **Verdict: weak as specified; one real gap exists.**

### User Value
**Unproven, and weakened by circumstance.** "One search for all bounties" has less value when there are fewer bounties and when the largest platform's catalog is not publicly listable. A developer's alternative — going to Algora, or reading a free curated list from OSS.Fund — is not demonstrably worse.

### Maintenance
**Hard, and structurally unrewarding.** Status/claim/payout truth is unavailable for the main source; label-based discovery requires permanent spam filtering; platform ToS changes force legal re-review; and the 1,000-result search cap plus 10 searches/min forces query partitioning just to keep an accurate inventory. **Verdict: high cost, low fidelity.**

### Risk
**Highest risks:** (1) source collapse already in progress; (2) GitHub AUP constraints on commercial re-publication and recruiter-adjacent use; (3) an already-shipping competitor; (4) ecosystem backlash if the product amplifies AI-slop contributions into review-starved repos. **Legal review is required** before any collector is written.

**Overall:** the specified product fails on *Data*, *Differentiation*, *User Value* and *Maintenance*, with *Technology* as the only clear pass. **Do not build as specified.** If the underlying interest is the ecosystem problem (paid OSS contribution), the evidence says the durable product is on the **maintainer/trust side**, not the aggregation side — and that should be validated with maintainers before any code is written.

---

# What I would investigate next before writing a single line of code

1. **Measure the real inventory by hand.** Take the 556 open `label:"💎 Bounty"` issues (and a sample of the 4,396 `label:bounty`), and manually classify 100: how many are real, funded, unclaimed, and how many distinct platforms do they come from? This single exercise decides the entire thesis. *(Blocked in this environment only by effort, not access.)*
2. **Get human answers from the two communities this product serves** — 20–30 maintainers and 20–30 bounty hunters: "how do you find paid work / how do you attract contributors today?" This is the demand question I could not measure. Ask specifically about the AI-slop dynamic; it changes the product's framing.
3. **Re-verify Opire, Boss.dev and BountySource** from an unrestricted network (they were unreachable here) — if they are dead too, the multi-platform premise is finished.
4. **Read GitHub ToS §H (API Terms) in full and get a legal read on AUP §6/§7** for a monetized index + email alerting. Do not write a collector first.
5. **Ask Algora directly** (they are an AGPL, self-hostable, publicly reachable team): is third-party indexing of bounties permitted, is the `bounty.list` endpoint intentionally stubbed, and is there any partner/feed path? The answer to this changes feasibility from "no" to "maybe" instantly.
6. **Use BountyOS as a product, hands-on.** Its pricing, its real data coverage, and how it handles unverifiable money/claims will tell you more about the market than any desk research. If it is thin, the market is thin; if it is good, the window is closed.
7. **Validate the one surviving differentiator with 10 maintainers:** "would you pay for a tool that filters out low-quality/AI-generated contributions and tells you how safe an outside contributor is?" If yes, the product is a maintainer tool, not a bounty search engine — and that is a different company.
8. **Quantify the API budget:** with the 1,000-result cap and secondary limits, how many repositories can a GitHub App installation realistically keep fresh at 5,000–12,500 calls/hour? Model it before designing the schema around "all of GitHub".
9. **Check whether the "bounty" label is shifting to a new convention** in 2026 (e.g. comment commands) by sampling recently-created bounty issues across platforms — if the convention moved, existing competitors' label-based pipelines are stale, which is a (small) opening.
10. **Decide the legal entity/framing question deliberately:** is this a nonprofit/public-good ("research/archival" framing under AUP §7) or a commercial product? The AUP language makes those two paths meaningfully different, and choosing late is the most expensive mistake available here.

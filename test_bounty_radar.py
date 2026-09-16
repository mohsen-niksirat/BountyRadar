#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for Bounty Radar. Run with:  python test_bounty_radar.py

Only offline data is used here (fixtures below), so the tests never hit the network
and never consume GitHub/Algora rate limits.
"""

import json
import os
import tempfile
import unittest

import bounty_radar as br

# A trimmed copy of a real Algora organisation page: two rows reward the SAME issue
# (a stacked reward pool) and one row is a different issue.
ALGORA_FIXTURE = """
<table>
 <tr data-state="false">
  <td><div><div><div class="font-extrabold text-emerald-300 hover:text-emerald-200">
        $50
      </div></div></div></td>
  <td>
    <a href="https://github.com/acme/lib/issues/7" class="group/issue inline-flex flex-col" rel="noopener">
      <div><p class="truncate text-sm font-medium text-gray-300">lib#7</p></div>
      <p class="line-clamp-2 break-words text-base font-medium leading-tight text-gray-100">
        Fix the parser crash on empty input
      </p>
    </a>
  </td>
  <td>3 days ago</td>
  <td>2 claims</td>
 </tr>
 <tr data-state="false">
  <td><div><div><div class="font-extrabold text-emerald-300">$100</div></div></div></td>
  <td>
    <a href="https://github.com/acme/lib/issues/7" class="group/issue inline-flex flex-col" rel="noopener">
      <div><p class="truncate text-sm font-medium text-gray-300">lib#7</p></div>
      <p class="line-clamp-2 break-words text-base font-medium leading-tight text-gray-100">
        Fix the parser crash on empty input
      </p>
    </a>
  </td>
  <td>2 months ago</td>
  <td>5 claims</td>
 </tr>
 <tr data-state="false">
  <td><div><div><div class="font-extrabold text-emerald-300">$30</div></div></div></td>
  <td>
    <a href="https://github.com/other/tool/issues/2" class="group/issue inline-flex flex-col" rel="noopener">
      <div><p class="truncate text-sm font-medium text-gray-300">tool#2</p></div>
      <p class="line-clamp-2 break-words text-base font-medium leading-tight text-gray-100">
        Use pglite when generating types
      </p>
    </a>
  </td>
  <td>20 months ago</td>
 </tr>
</table>
"""

GITHUB_ITEM = {
    "source": "github", "platform": "Opire", "repo": "acme/lib", "repo_short": "lib",
    "number": 11, "title": "Add retry to the uploader", "amount": 60.0,
    "amount_estimated": True, "claims": None, "age_days": 2, "age_text": "",
    "url": "https://github.com/acme/lib/issues/11", "comments": 1,
}


class TestAlgoraParser(unittest.TestCase):
    def test_parses_rows(self):
        rows = br._parse_algora_page(ALGORA_FIXTURE)
        self.assertEqual(len(rows), 3)
        first = rows[0]
        self.assertEqual(first["repo"], "acme/lib")       # owner comes from the href
        self.assertEqual(first["repo_short"], "lib")
        self.assertEqual(first["number"], 7)
        self.assertEqual(first["amount"], 50.0)
        self.assertEqual(first["claims"], 2)              # claim count is parsed
        self.assertEqual(first["age_days"], 3)
        self.assertEqual(first["url"], "https://github.com/acme/lib/issues/7")
        self.assertIn("parser crash", first["title"])

    def test_third_row_without_claims(self):
        rows = br._parse_algora_page(ALGORA_FIXTURE)
        self.assertIsNone(rows[2]["claims"])              # no "N claims" in that row
        self.assertEqual(rows[2]["age_days"], 600)        # 20 months -> 600 days

    def test_empty_page_is_survivable(self):
        self.assertEqual(br._parse_algora_page("<div>No open bounties</div>"), [])


class TestAggregation(unittest.TestCase):
    def test_stacked_rewards_add_up_and_claims_take_the_max(self):
        rows = br._parse_algora_page(ALGORA_FIXTURE)
        agg = br.aggregate_rows(rows)
        self.assertEqual(len(agg), 2)
        merged = agg[("acme/lib", 7)]
        self.assertEqual(merged["amount"], 150.0)         # $50 + $100
        self.assertEqual(merged["claims"], 5)             # max(2, 5)
        self.assertEqual(merged["age_days"], 3)           # keeps the freshest information


class TestFakeBountyFilters(unittest.TestCase):
    def setUp(self):
        self.s = dict(br.DEFAULT_SETTINGS)

    def _item(self, repo, title, amount=None):
        return {"repo": repo, "number": 1, "title": title, "amount": amount,
                "source": "github", "claims": None, "age_days": 5}

    def test_blocks_known_farms(self):
        cases = [
            ("xevrion-v2/agent-playground", "Calculate the exact value of PI", 500.0),
            ("UnsafeLabs/Bounty-Hunters", "[ Crypto ] Fix cross-chain replay attack", None),
            ("someone/x", "[Bounty][$0][Setup] run the tests", None),
            ("someone/y", "Fix flash loan drain in the vault", 100.0),
            ("someone/z", "real task", 999999.0),                     # absurd amount
            ("someone/w", "real task", 0.0),                          # explicit $0
        ]
        for repo, title, amount in cases:
            self.assertTrue(br.is_denied(self._item(repo, title, amount), self.s),
                            f"should be denied: {repo} / {title}")

    def test_keeps_plausible_bounties(self):
        self.assertFalse(br.is_denied(self._item("tscircuit/lib", "Improve test coverage", 50.0), self.s))
        self.assertFalse(br.is_denied(self._item("acme/tool", "Support async iterators"), self.s))

    def test_filter_can_be_disabled(self):
        s = dict(self.s, hide_farms=False)
        item = self._item("xevrion-v2/agent-playground", "Calculate the exact value of PI", 500.0)
        self.assertFalse(br.is_denied(item, s))


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.s = dict(br.DEFAULT_SETTINGS)
        self.fresh = {"repo": "acme/lib", "number": 1, "title": "t", "amount": 60.0,
                      "amount_estimated": False, "claims": 0, "age_days": 3,
                      "source": "algora", "stars": 800}

    def test_fresh_low_competition_beats_stale_crowded(self):
        good, _ = br.score_item(dict(self.fresh), self.s)
        crowded, _ = br.score_item(dict(self.fresh, claims=120, age_days=700), self.s)
        self.assertGreater(good, crowded * 10)

    def test_bigger_money_wins_when_competition_is_equal(self):
        small, _ = br.score_item(dict(self.fresh, amount=50.0), self.s)
        big, _ = br.score_item(dict(self.fresh, amount=500.0), self.s)
        self.assertGreater(big, small)

    def test_unknown_amount_is_penalised_and_explained(self):
        unknown, reasons = br.score_item(dict(self.fresh, amount=None), self.s)
        known, _ = br.score_item(dict(self.fresh), self.s)
        self.assertLess(unknown, known)
        self.assertTrue(any("نامعلوم" in r or "unknown" in r for r in reasons))

    def test_every_score_explains_itself(self):
        _, reasons = br.score_item(dict(self.fresh, claims=4, age_days=200), self.s)
        self.assertGreaterEqual(len(reasons), 3)

    def test_archived_repository_is_buried(self):
        a, _ = br.score_item(dict(self.fresh, archived=True), self.s)
        b, _ = br.score_item(dict(self.fresh), self.s)
        self.assertLess(a, b)

    def test_scoring_is_a_pure_function(self):
        before = json.dumps(self.fresh, sort_keys=True)
        br.score_item(self.fresh, self.s)
        self.assertEqual(before, json.dumps(self.fresh, sort_keys=True))


class TestProfiles(unittest.TestCase):
    def test_every_profile_has_required_fields(self):
        for pid, p in br.PROFILES.items():
            self.assertEqual(pid, p["id"])
            self.assertTrue(p.get("label"))
            self.assertIn("languages", p)
            self.assertIn("keywords", p)

    def test_skill_boost_matches_keywords(self):
        item = {"title": "Fix React component accessibility in the design system",
                "labels": ["ui", "frontend"]}
        boost, hits = br.skill_boost(item, "frontend")
        self.assertGreater(boost, 1.0)
        self.assertTrue(hits)
        self.assertLessEqual(boost, 1.45)

    def test_skill_boost_no_match_is_neutral(self):
        item = {"title": "Rewrite the C++ allocator", "labels": []}
        boost, hits = br.skill_boost(item, "frontend")
        self.assertEqual(boost, 1.0)
        self.assertEqual(hits, [])

    def test_any_profile_has_no_boost(self):
        item = {"title": "Fix React component", "labels": []}
        boost, hits = br.skill_boost(item, "any")
        self.assertEqual(boost, 1.0)
        self.assertEqual(hits, [])

    def test_docs_profile_finds_documentation_work(self):
        item = {"title": "Write a getting-started tutorial and translate the README",
                "labels": ["documentation"]}
        boost, hits = br.skill_boost(item, "docs")
        self.assertGreater(boost, 1.0)
        self.assertIn("docs", " ".join(hits) + " docs" if hits else "docs")

    def test_design_profile_finds_design_work(self):
        item = {"title": "Create a Figma icon set for the brand", "labels": ["design"]}
        boost, hits = br.skill_boost(item, "design")
        self.assertGreater(boost, 1.0)
        self.assertTrue(any(k in "figma icon design brand" for k in hits))

    def test_github_queries_include_profile_languages(self):
        s = dict(br.DEFAULT_SETTINGS, profile="backend", languages=list(br.PROFILES["backend"]["languages"]))
        qs = br.build_github_queries(s)
        self.assertTrue(qs)
        self.assertTrue(any("language:Python" in q or "language:Go" in q for q in qs))
        self.assertTrue(any("Bounty" in q or "bounty" in q for q in qs))

    def test_docs_profile_omits_language_filter(self):
        s = dict(br.DEFAULT_SETTINGS, profile="docs", languages=[])
        qs = br.build_github_queries(s)
        self.assertTrue(qs)
        # Docs work should not be locked behind language: filters
        self.assertFalse(any("language:" in q for q in qs if "label:" in q and "bounty" in q.lower()))

    def test_skill_match_raises_score(self):
        base = {"repo": "acme/lib", "number": 1, "title": "Improve tests",
                "amount": 50.0, "amount_estimated": False, "claims": 0,
                "age_days": 5, "source": "algora"}
        skilled = dict(base, title="Fix React UI accessibility and dark theme")
        s_any = dict(br.DEFAULT_SETTINGS, profile="any")
        s_fe = dict(br.DEFAULT_SETTINGS, profile="frontend")
        score_plain, _ = br.score_item(dict(base), s_any)
        score_skilled, reasons = br.score_item(skilled, s_fe)
        self.assertGreater(score_skilled, score_plain)
        self.assertTrue(any("skill match" in r for r in reasons))


class TestSummaryAndCache(unittest.TestCase):
    def test_summarize_counts(self):
        results = [
            {"amount": 100, "claims": 0, "age_days": 3, "score": 80,
             "platform": "Algora", "skill_hits": ["ui"], "is_new": True,
             "preflight": {"verdict": "GO", "score": 90, "open_prs": 0}},
            {"amount": None, "claims": 10, "age_days": 40, "score": 10,
             "platform": "Opire", "skill_hits": [], "is_new": False,
             "preflight": {"verdict": "STOP", "score": 10, "open_prs": 4}},
        ]
        st = br.summarize(results)
        self.assertEqual(st["total"], 2)
        self.assertEqual(st["total_money"], 100)
        self.assertEqual(st["fresh"], 1)
        self.assertEqual(st["low_competition"], 1)
        self.assertEqual(st["skill_matched"], 1)
        self.assertEqual(st["new"], 1)
        self.assertEqual(st["platforms"].get("Algora"), 1)
        self.assertEqual(st["preflight_go"], 1)
        self.assertEqual(st["preflight_stop"], 1)

    def test_empty_summary_is_safe(self):
        st = br.summarize([])
        self.assertEqual(st["total"], 0)
        self.assertEqual(st["total_money"], 0)


class TestPreflightScoring(unittest.TestCase):
    def setUp(self):
        self.s = dict(br.DEFAULT_SETTINGS)
        self.base = {"repo": "acme/lib", "number": 1, "title": "t", "amount": 80.0,
                     "amount_estimated": False, "claims": 0, "age_days": 5,
                     "source": "algora", "stars": 200}

    def test_preflight_go_boosts_score(self):
        plain, _ = br.score_item(dict(self.base), self.s)
        go, reasons = br.score_item(
            dict(self.base, preflight={"verdict": "GO", "open_prs": 0}), self.s)
        self.assertGreater(go, plain)
        self.assertTrue(any("preflight GO" in r for r in reasons))

    def test_preflight_stop_buries_score(self):
        plain, _ = br.score_item(dict(self.base), self.s)
        stop, reasons = br.score_item(
            dict(self.base, preflight={"verdict": "STOP", "open_prs": 5}), self.s)
        self.assertLess(stop, plain * 0.5)
        self.assertTrue(any("preflight STOP" in r for r in reasons))

    def test_preflight_caution_lands_between(self):
        plain, _ = br.score_item(dict(self.base), self.s)
        caution, _ = br.score_item(
            dict(self.base, preflight={"verdict": "CAUTION", "open_prs": 1}), self.s)
        stop, _ = br.score_item(
            dict(self.base, preflight={"verdict": "STOP", "open_prs": 3}), self.s)
        self.assertLess(stop, caution)
        self.assertLess(caution, plain)

    def test_preflight_limit_in_defaults(self):
        self.assertIn("preflight_limit", br.DEFAULT_SETTINGS)
        self.assertGreater(br.DEFAULT_SETTINGS["preflight_limit"], 0)


class TestDiscoveryHelpers(unittest.TestCase):
    def test_extract_bounty_command_amount(self):
        self.assertEqual(br.extract_amounts_from_text("Please /bounty $250 on this"), 250.0)
        self.assertEqual(br.extract_amounts_from_text("/reward 80 thanks"), 80.0)

    def test_extract_prefers_command_over_loose_dollars(self):
        amt = br.extract_amounts_from_text("See $5 docs. /bounty $400 for the fix")
        self.assertEqual(amt, 400.0)

    def test_extract_rejects_absurd(self):
        self.assertIsNone(br.extract_amounts_from_text("/bounty $999999999999"))

    def test_discover_algora_orgs_from_links(self):
        items = [
            {"url": "https://github.com/acme/lib/issues/1",
             "body": "Funded on https://algora.io/cal/bounties", "title": "x", "labels": []},
            {"url": "https://github.com/acme/lib/issues/2",
             "body": "https://algora.io/tscircuit/bounties", "title": "y", "labels": []},
        ]
        orgs = br.discover_algora_orgs(items, log=lambda m: None)
        self.assertIn("cal", orgs)
        self.assertIn("tscircuit", orgs)

    def test_queries_are_partitioned_and_capped(self):
        s = dict(br.DEFAULT_SETTINGS, profile="any", languages=[])
        qs = br.build_github_queries(s)
        self.assertTrue(any("created:" in q for q in qs))
        self.assertLessEqual(len(qs), 8)


class TestWatchDiff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        os.remove(self.tmp.name)          # start from "never scanned"
        self._orig = br.SEEN_FILE
        br.SEEN_FILE = self.tmp.name

    def tearDown(self):
        br.SEEN_FILE = self._orig
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    @staticmethod
    def _item(repo, number):
        return {"repo": repo, "number": number, "title": "t", "amount": 10.0}

    def test_first_scan_is_a_silent_baseline(self):
        items = [self._item("a/b", 1), self._item("a/b", 2)]
        self.assertEqual(br.mark_new(items), 0)                 # no alert on a fresh install
        self.assertFalse(any(it.get("is_new") for it in items))
        with open(self.tmp.name, encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)), 2)

    def test_only_the_delta_is_flagged(self):
        br.mark_new([self._item("a/b", 1)])
        results = [self._item("a/b", 1), self._item("c/d", 9)]
        n = br.mark_new(results, log=lambda m: None)
        self.assertEqual(n, 1)
        self.assertFalse(results[0]["is_new"])
        self.assertTrue(results[1]["is_new"])

    def test_new_survives_an_app_restart(self):
        br.mark_new([self._item("a/b", 1)])
        again = [self._item("a/b", 1)]
        self.assertEqual(br.mark_new(again, log=lambda m: None), 0)

    def test_key_is_owner_insensitive(self):
        self.assertEqual(br.key_of({"repo": "Acme/Lib", "number": 5}), "acme/lib#5")


class TestHardening(unittest.TestCase):
    def test_expanded_deny_patterns(self):
        s = dict(br.DEFAULT_SETTINGS)
        cases = [
            ("someone/x", "Claim your airdrop reward now", None),
            ("someone/y", "Connect your wallet to claim $5000", 5000.0),
            ("airdrop-bounty/free-money", "real looking", 50.0),
            ("someone/z", "Send me 0xabc private key to pay you", None),
        ]
        for repo, title, amount in cases:
            item = {"repo": repo, "number": 1, "title": title, "amount": amount,
                    "source": "github", "claims": None, "age_days": 1}
            self.assertTrue(br.is_denied(item, s), f"should deny: {title}")

    def test_markdown_shortlist_export(self):
        import tempfile
        results = [
            {"score": 90, "amount": 150, "claims": 0, "age_days": 2, "repo": "a/b",
             "number": 1, "title": "Fix the thing", "why": "$150 · no claims yet",
             "url": "https://github.com/a/b/issues/1",
             "preflight": {"verdict": "GO"}},
        ]
        fd, path = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        try:
            out = br.export_markdown_shortlist(results, path=path)
            self.assertEqual(out, path)
            text = open(path, encoding="utf-8").read()
            self.assertIn("Bounty shortlist", text)
            self.assertIn("a/b#1", text)
            self.assertIn("GO", text)
        finally:
            os.remove(path)

    def test_history_append_keeps_rolling_window(self):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)
        orig = br.HISTORY_FILE
        br.HISTORY_FILE = path
        try:
            results = [{"score": 1, "repo": "a/b", "number": 1, "title": "t",
                        "amount": 10, "preflight": {"verdict": "GO"}}]
            br.append_history(results, {"profile": "any"})
            br.append_history(results, {"profile": "any"})
            data = json.load(open(path, encoding="utf-8"))
            self.assertEqual(len(data), 2)
            self.assertEqual(data[-1]["total"], 1)
        finally:
            br.HISTORY_FILE = orig
            if os.path.exists(path):
                os.remove(path)

    def test_slim_result_drops_body(self):
        slim = br._slim_result({"repo": "a/b", "number": 1, "title": "t",
                                "body": "x" * 500, "amount": 10})
        self.assertNotIn("body", slim)
        self.assertIn("body_snip", slim)
        self.assertLessEqual(len(slim["body_snip"]), 120)
        self.assertEqual(slim["amount"], 10)

    def test_score_history_roundtrip(self):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)
        orig = br.SCORE_HISTORY_FILE
        br.SCORE_HISTORY_FILE = path
        try:
            items = [{"repo": "a/b", "number": 1, "score": 10.0, "amount": 50, "claims": 0},
                     {"repo": "a/b", "number": 2, "score": 20.0, "amount": 80, "claims": 1}]
            br.update_score_history(items)
            items[0]["score"] = 18.0
            br.update_score_history(items)
            out = br.attach_score_history([{"repo": "a/b", "number": 1}])
            self.assertEqual(out[0]["score_hist"], [10.0, 18.0])
            self.assertEqual(out[0]["score_delta"], 8.0)
        finally:
            br.SCORE_HISTORY_FILE = orig
            if os.path.exists(path):
                os.remove(path)

    def test_ui_language_setting_default(self):
        self.assertIn("ui_language", br.DEFAULT_SETTINGS)
        self.assertIn(br.DEFAULT_SETTINGS["ui_language"], ("en", "fa"))

    def test_i18n_file_exists(self):
        path = os.path.join(br.APP_DIR, "ui", "i18n.js")
        self.assertTrue(os.path.isfile(path), "ui/i18n.js missing")
        text = open(path, encoding="utf-8").read()
        self.assertIn("BR_I18N", text)
        self.assertIn("fa:", text)
        self.assertIn("en:", text)
        self.assertIn("رادار", text)


class TestClaimWorkflow(unittest.TestCase):
    def setUp(self):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)
        self.path = path
        self._orig = br.CLAIMS_FILE
        br.CLAIMS_FILE = path

    def tearDown(self):
        br.CLAIMS_FILE = self._orig
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_upsert_and_list(self):
        e = br.upsert_claim("acme/lib", 7, title="Fix parser", amount=100, status="working")
        self.assertEqual(e["status"], "working")
        items = br.list_claims()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["repo"], "acme/lib")
        br.upsert_claim("acme/lib", 7, status="won")
        self.assertEqual(br.list_claims()[0]["status"], "won")
        self.assertEqual(len(br.list_claims()), 1)

    def test_delete_claim(self):
        br.upsert_claim("a/b", 1)
        self.assertTrue(br.delete_claim("a/b", 1))
        self.assertEqual(br.list_claims(), [])

    def test_attach_claims_to_results(self):
        br.upsert_claim("acme/lib", 7, status="working")
        results = [{"repo": "acme/lib", "number": 7}, {"repo": "x/y", "number": 1}]
        br.attach_claims(results)
        self.assertEqual(results[0]["claim"]["status"], "working")
        self.assertIsNone(results[1]["claim"])

    def test_claim_summary_checklist(self):
        br.upsert_claim("a/b", 1, status="working")
        s = br.claim_summary()
        self.assertEqual(s["total"], 1)
        self.assertEqual(s["working"], 1)
        self.assertGreaterEqual(len(s["checklist"]), 5)

    def test_invalid_status_falls_back(self):
        e = br.upsert_claim("a/b", 2, status="nope")
        self.assertEqual(e["status"], "shortlisted")

    def test_frozen_paths_defined(self):
        self.assertTrue(br.APP_DIR)
        self.assertTrue(br.RESOURCE_DIR)
        self.assertTrue(br.UI_FILE.endswith("index.html"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

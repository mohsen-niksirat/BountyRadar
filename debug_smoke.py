# -*- coding: utf-8 -*-
"""Quick debug/smoke harness for Bounty Radar Pro. Offline only."""
import json
import sys
import traceback

import bounty_radar as br


def check(name, fn):
    try:
        out = fn()
        print(f"OK  {name}: {out}")
        return True
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def main():
    ok = True
    ok &= check("profiles", lambda: len(br.PROFILES))
    ok &= check("defaults", lambda: "preflight_limit" in br.DEFAULT_SETTINGS)

    def purity():
        it = {"repo": "a/b", "number": 1, "title": "Fix UI", "amount": 50.0,
              "amount_estimated": False, "claims": 0, "age_days": 3, "source": "algora"}
        before = json.dumps(it, sort_keys=True)
        s, reasons = br.score_item(it, dict(br.DEFAULT_SETTINGS, profile="frontend"))
        assert before == json.dumps(it, sort_keys=True), "score_item mutated item"
        assert s > 0 and reasons
        return f"score={s} reasons={len(reasons)}"
    ok &= check("score_pure", purity)

    def queries():
        qs = br.build_github_queries({**br.DEFAULT_SETTINGS, "profile": "docs", "languages": []})
        assert qs and all(isinstance(q, str) for q in qs)
        return len(qs)
    ok &= check("queries", queries)

    def parse():
        page = (
            '<div>$40</div></div>'
            '<a href="https://github.com/acme/lib/issues/9" class="x">'
            '<p class="line-clamp-2 break-words">Fix parser</p></a>'
            "3 days ago"
            "1 claim"
        )
        rows = br._parse_algora_page(page)
        assert rows and rows[0]["amount"] == 40.0 and rows[0]["number"] == 9
        return rows[0]["amount"]
    ok &= check("algora_parse", parse)

    def deny():
        item = {"repo": "xevrion-v2/x", "number": 1, "title": "Calculate the exact value of PI",
                "amount": 5.0, "source": "github", "claims": None, "age_days": 1}
        return br.is_denied(item, br.DEFAULT_SETTINGS)
    ok &= check("deny_farm", deny)

    ok &= check("export_md", lambda: callable(br.export_markdown_shortlist))
    ok &= check("history", lambda: callable(br.append_history))
    ok &= check("web_ui", lambda: callable(br.run_web_ui))
    ok &= check("preflight_offline", lambda: callable(br.preflight_item))
    ok &= check("skill_boost", lambda: br.skill_boost({"title": "React a11y UI", "labels": []}, "frontend")[0] > 1)

    # cache key stability
    ok &= check("cache_key", lambda: br._cache_key(br.DEFAULT_SETTINGS) == br._cache_key(dict(br.DEFAULT_SETTINGS)))

    print("\nALL_OK" if ok else "\nHAS_FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

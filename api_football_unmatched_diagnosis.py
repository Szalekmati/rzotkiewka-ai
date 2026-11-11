"""Aggregate-only diagnosis of unexplained matches in two-source research.

Never prints individual fixtures or provider team names, never changes forecasts.
Read-only: two API-FOOTBALL fixture requests at most on explicit invocation.
"""
import argparse
from datetime import date
import os

from api_football_probe import api_get, verify_subscription
from api_football_league_catalog import check_quota
from api_football_crosscheck import (
    SOURCES, SEASON, read_openfootball_matches, read_api_matches,
    reconcile
)
from openfootball_history_audit import fetch_text


def split_unmatched(left, right):
    """Exact normalised ordered club pair, date tolerance 1 day.

    Returns unpaired rows and ambiguity count. Does NOT use scores to match.
    """
    remaining = list(right)
    unpaired = []
    ambiguous = 0
    matches = 0
    for rec in left:
        matches_idx = [
            i for i, cand in enumerate(remaining)
            if cand[1:3] == rec[1:3]
            and abs((cand[0] - rec[0]).days) <= 1
        ]
        if len(matches_idx) == 1:
            remaining.pop(matches_idx[0])
            matches += 1
        else:
            if len(matches_idx) > 1:
                ambiguous += 1
            unpaired.append(rec)
    return unpaired, remaining, matches, ambiguous


def classify_unpaired(records, other, all_other):
    """Mutually exclusive evidence categories, not automatic explanations."""
    home_names = {r[1] for r in all_other}
    away_names = {r[2] for r in all_other}
    categories = {
        "pair_other_date": 0,
        "both_names_exist": 0,
        "only_home_name": 0,
        "only_away_name": 0,
        "neither_name": 0,
    }
    for rec in records:
        d, home, away, _ = rec
        if any(x[1:3] == (home, away) and abs((x[0] - d).days) > 1
               for x in other):
            categories["pair_other_date"] += 1
        elif home in home_names and away in away_names:
            categories["both_names_exist"] += 1
        elif home in home_names:
            categories["only_home_name"] += 1
        elif away in away_names:
            categories["only_away_name"] += 1
        else:
            categories["neither_name"] += 1
    assert sum(categories.values()) == len(records)
    return categories


def diagnose(source, api):
    unmatched_source, unmatched_api, n_matched, ambiguity = split_unmatched(source, api)
    base = reconcile(source, api)
    if (base["matched"] != n_matched or
            base["source_unmatched"] != len(unmatched_source) or
            base["api_unmatched"] != len(unmatched_api) or
            base["ambiguous"] != ambiguity):
        raise RuntimeError("Diagnostyka jest niespojna z audytem bazowym.")
    source_all = {name for d, h, a, score in source for name in (h, a)}
    api_all = {name for d, h, a, score in api for name in (h, a)}
    return {
        "base": base,
        "source_unique_team_names": len(source_all),
        "api_unique_team_names": len(api_all),
        "shared_team_names": len(source_all & api_all),
        "unpaired_source": classify_unpaired(unmatched_source, unmatched_api, api),
        "unpaired_api": classify_unpaired(unmatched_api, unmatched_source, source),
    }


def run(start, end, key):
    check_quota(verify_subscription(api_get("status", key)), needed=2, reserve=100)
    print(f"Diagnoza dwoch zrodel, daty: {start} .. {end}. Maks. 2 zapytania API.")
    for league_id, name, spec in SOURCES:
        public_source = read_openfootball_matches(fetch_text(spec), start, end)
        payload = api_get("fixtures", key, {
            "league": str(league_id), "season": str(SEASON),
            "from": start.isoformat(), "to": end.isoformat(), "timezone": "UTC"
        })
        provider, skipped = read_api_matches(payload, league_id, SEASON, start, end)
        report = diagnose(public_source, provider)
        b = report["base"]
        print(f"{name}: pairs={b['matched']} of source={b['source_scores']} "
              f"and API={b['api_finals']}; agreement={b['same_score']} "
              f"disagreement={b['score_disagreements']} ambiguous={b['ambiguous']} "
              f"api_skipped={skipped}.")
        print(f"{name}: unique_normalized_team_names "
              f"source={report['source_unique_team_names']} "
              f"api={report['api_unique_team_names']} "
              f"shared={report['shared_team_names']}.")
        for side, labels in (("source", report["unpaired_source"]),
                             ("api", report["unpaired_api"])):
            details = " ".join(f"{k}={v}" for k, v in labels.items())
            print(f"{name} unpaired_{side}: {details}")
    print("Kategorie wskazuja jedynie dowody strukturalne. "
          "Nie przesadzaja przyczyny rozbieznosci ani nie potwierdzaja poprawnosci wynikow.")
    print("Bez publikowania rekordow ani nazw druzyn z API. Bez zmian LAB i prognoz.")


def main():
    p = argparse.ArgumentParser(description="Badanie 30 niedopasowanych meczow")
    p.add_argument("--from-date", default="2026-08-21")
    p.add_argument("--to-date", default="2026-08-31")
    args = p.parse_args()
    try:
        start, end = date.fromisoformat(args.from_date), date.fromisoformat(args.to_date)
        if (start < date(2026, 8, 1) or end > date(2026, 10, 15)
                or start > end or (end-start).days > 13):
            raise ValueError("Dozwolone maks. 14 dni w okresie 01.08-15.10.2026.")
        run(start, end, os.environ.get("API_FOOTBALL_KEY", ""))
    except (OSError, RuntimeError, ValueError, UnicodeError) as e:
        # Avoid provider payloads or names in GitHub logs.
        p.exit(1, f"Diagnoza nieudana: {type(e).__name__}.\n")


if __name__ == "__main__":
    main()

"""Research-only proposals for club name mappings, never production aliases.

Use no match score when proposing identity. Two source snapshots are fetched
only by explicit, bounded workflow. Only aggregate counts are logged.
"""
from collections import Counter
from datetime import date
import argparse
import os

from api_football_crosscheck import (
    SEASON, SOURCES, clean_team, read_api_matches,
    read_openfootball_matches, reconcile
)
from api_football_probe import api_get, verify_subscription
from api_football_league_catalog import check_quota
from openfootball_history_audit import fetch_text

# Common words are excluded for uniqueness, not proof of identity.
# The registry is deliberately diagnostic-only; no alias is "approved".
FILLER = frozenset({
    "club", "rc", "rcd", "ca", "ud", "de", "del", "la", "el",
    "and", "of", "futbol", "balompie"
})
GENERIC = frozenset({"real", "city", "united", "athletic", "football", "deportivo"})


def tokens(name):
    if not isinstance(name, str):
        return frozenset()
    return frozenset(
        token for token in clean_team(name).split()
        if token not in FILLER and len(token) > 1
    )


def propose_names(source_names, api_names):
    """Only unique name-form candidates, never approved for predictions.

    No fixture results, IDs, outcomes or odds are used to infer name identity.
    Require at least one distinctive token occurring exactly once among names
    in BOTH rosters and subset of tokens (no edit-distance or fuzzy joining).
    """
    source_names = set(source_names)
    api_names = set(api_names)
    if "" in source_names or "" in api_names:
        raise ValueError("Pusta nazwa klubu.")
    source_tokens = {n: tokens(n) for n in source_names}
    api_tokens = {n: tokens(n) for n in api_names}
    if any(not x for x in (*source_tokens.values(), *api_tokens.values())):
        raise ValueError("Nieczytelna nazwa klubu.")
    src_use = Counter(t for group in source_tokens.values() for t in group)
    api_use = Counter(t for group in api_tokens.values() for t in group)
    exact = source_names & api_names
    # All exact names are already matched; never override or point aliases to them.
    source_left = source_names - exact
    api_left = api_names - exact
    edges = {}
    for src in source_left:
        s = source_tokens[src]
        options = []
        for api in api_left:
            a = api_tokens[api]
            shared = s & a
            unique = {t for t in shared if len(t) >= 5 and t not in GENERIC
                      and src_use[t] == 1 and api_use[t] == 1}
            if unique and (s <= a or a <= s):
                options.append(api)
        edges[src] = options
    reverse = Counter(api for options in edges.values() for api in options)
    candidates = {src: options[0] for src, options in edges.items()
                  if len(options) == 1 and reverse[options[0]] == 1}
    return candidates, {
        "exact_team_names": len(exact),
        "source_names": len(source_names),
        "api_names": len(api_names),
        "unique_candidates": len(candidates),
        "source_names_without_proposal": len(source_left) - len(candidates),
        "api_names_without_proposal": len(api_left) - len(candidates),
        "ambiguous_source_names": sum(1 for o in edges.values() if len(o) > 1),
        "ambiguous_api_names": sum(1 for n in reverse.values() if n > 1),
    }


def compare_candidate_pairs(source, api, aliases):
    """Candidate-only projected pairs; no approval, no changes to model."""
    converted = [
        (d, aliases.get(home, home), aliases.get(away, away), score)
        for d, home, away, score in source
    ]
    return reconcile(converted, api)


def evaluate(source, api):
    source_names = {n for d, h, a, score in source for n in (h, a)}
    api_names = {n for d, h, a, score in api for n in (h, a)}
    alias_map, coverage = propose_names(source_names, api_names)
    baseline = reconcile(source, api)
    tentative = compare_candidate_pairs(source, api, alias_map)
    if tentative["matched"] < baseline["matched"]:
        raise RuntimeError("Kandydaci pogorszyli porownanie; przerwano.")
    return coverage, baseline, tentative


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--from-date", default="2026-08-21")
    p.add_argument("--to-date", default="2026-08-31")
    args = p.parse_args()
    try:
        start, end = date.fromisoformat(args.from_date), date.fromisoformat(args.to_date)
        if (start < date(2026, 8, 1) or end > date(2026, 10, 15)
                or start > end or (end-start).days > 13):
            raise ValueError("Maksymalnie 14 dni w ograniczonym oknie archiwum.")
        key = os.environ.get("API_FOOTBALL_KEY", "")
        status = verify_subscription(api_get("status", key))
        check_quota(status, needed=2, reserve=100)
        print("Badanie tozsamosci klubow: bez zapisu aliasow, wynikow, nazw i danych API.")
        print(f"Weryfikowany zakres: {start} do {end}, zuzycie API przed audytem: {status['used_today']}.")
        for lid, label, spec in SOURCES:
            historical = read_openfootball_matches(fetch_text(spec), start, end)
            payload = api_get("fixtures", key, {
                "league": str(lid), "season": str(SEASON),
                "from": start.isoformat(), "to": end.isoformat(), "timezone": "UTC"
            })
            provider, skipped = read_api_matches(payload, lid, SEASON, start, end)
            coverage, base, tentative = evaluate(historical, provider)
            print(
                f"{label}: {coverage}; "
                f"baseline_pairs={base['matched']}, baseline_agreed={base['same_score']}, "
                f"candidate_pairs={tentative['matched']}, "
                f"candidate_agreed={tentative['same_score']}, "
                f"candidate_disagreed={tentative['score_disagreements']}, "
                f"candidate_unpaired_source={tentative['source_unmatched']}, "
                f"candidate_unpaired_api={tentative['api_unmatched']}, "
                f"candidate_date_shifts={tentative['day_shifts']}, "
                f"api_nonfinal={skipped}"
            )
        print("Kandydaci na aliasy NIE sa zatwierdzonymi mapowaniami. "
              "Wynik moze przypadkowo poprawiac parowanie; wymagane niezalezne sprawdzenie "
              "tozsamosci klubow. Dane i raporty pojedynczych meczow nie sa publikowane.")
    except (RuntimeError, ValueError, OSError, UnicodeError) as exc:
        p.exit(1, f"Audyt identyfikatorow: {type(exc).__name__}.\n")


if __name__ == "__main__":
    main()

"""Holdout-only audit of unapproved club-name candidates.

Training and validation use DIFFERENT, fixed fixture date windows. Club-name
candidates are generated from training rosters only; validation cannot update
them. Runs only on explicit GitHub Actions invocation. No raw provider data
or team names are logged, saved, published, or fed into prediction models.

This is NOT a forward-time prediction backtest. OpenFootball snapshots were
committed after both windows and are independent research references only.
"""
from datetime import date
import os
import sys

from api_football_alias_candidates import propose_names, compare_candidate_pairs
from api_football_crosscheck import (
    SOURCES, SEASON, read_openfootball_matches, read_api_matches, reconcile,
)
from api_football_league_catalog import check_quota
from api_football_probe import api_get, verify_subscription
from openfootball_history_audit import fetch_text

TRAIN_START = date(2026, 8, 21)
TRAIN_END = date(2026, 8, 31)
HOLDOUT_START = date(2026, 9, 4)
HOLDOUT_END = date(2026, 9, 14)
MAX_FIXTURE_CALLS = 4


def assert_windows(train_start, train_end, test_start, test_end):
    """Strict historical disjoint windows; independent holdout protocol."""
    if not (isinstance(train_start, date) and isinstance(train_end, date)
            and isinstance(test_start, date) and isinstance(test_end, date)):
        raise ValueError("Niepoprawna data w protokole.")
    if train_start > train_end or test_start > test_end or train_end >= test_start:
        raise ValueError("Okna uczenia aliasow i kontroli nakladaja sie.")
    if (train_end - train_start).days > 13 or (test_end - test_start).days > 13:
        raise ValueError("Kazde okno musi miec maksymalnie 14 dni.")
    if test_end > date(2026, 10, 15):
        raise ValueError("Proba wykracza poza przegladany snapshot 15.10.2026.")


def roster(rows):
    return {name for _date, home, away, _score in rows for name in (home, away)}


def score_holdout(train_source, train_api, test_source, test_api):
    """No validation outcomes or club names enter training proposal function."""
    if not train_source or not train_api:
        raise RuntimeError("Zbyt mala proba uczaca; nie tworzymy mapowania.")
    if not test_source or not test_api:
        raise RuntimeError("Pusta proba kontrolna; nie deklarujemy sukcesu.")
    # These are the ONLY arguments to the candidate generator.
    aliases, coverage = propose_names(roster(train_source), roster(train_api))
    baseline = reconcile(test_source, test_api)
    candidate = compare_candidate_pairs(test_source, test_api, aliases)
    if candidate["matched"] < baseline["matched"]:
        raise RuntimeError("Mapa z uczenia pogorszyla dopasowanie testu.")
    known_source = roster(train_source)
    unknown_holdout = roster(test_source) - known_source
    return {
        "proposals_training_only": len(aliases),
        "training_source_games": len(train_source),
        "training_api_games": len(train_api),
        "holdout_source_games": len(test_source),
        "holdout_api_games": len(test_api),
        "holdout_new_source_names": len(unknown_holdout),
        "holdout_baseline_matches": baseline["matched"],
        "holdout_candidate_matches": candidate["matched"],
        "holdout_agree": candidate["same_score"],
        "holdout_disagree": candidate["score_disagreements"],
        "holdout_day_shifts": candidate["day_shifts"],
        "holdout_ambiguous": candidate["ambiguous"],
        "holdout_source_unpaired": candidate["source_unmatched"],
        "holdout_api_unpaired": candidate["api_unmatched"],
    }


def api_window(league_id, start, end, key):
    data = api_get("fixtures", key, {
        "league": str(league_id), "season": str(SEASON),
        "from": start.isoformat(), "to": end.isoformat(),
        "timezone": "UTC",
    })
    matches, skipped = read_api_matches(data, league_id, SEASON, start, end)
    return matches, skipped


def run(key):
    assert_windows(TRAIN_START, TRAIN_END, HOLDOUT_START, HOLDOUT_END)
    status = verify_subscription(api_get("status", key))
    if MAX_FIXTURE_CALLS != 2 * len(SOURCES):
        raise RuntimeError("Bledny budzet wywolan audytu.")
    check_quota(status, needed=MAX_FIXTURE_CALLS, reserve=100)
    print("RZOTKIEWKA: niezalezny test okresowy kandydatow aliasow.")
    print(f"Uczymy tylko z: {TRAIN_START} .. {TRAIN_END}; "
          f"kontrolujemy bez poprawiania nazw: {HOLDOUT_START} .. {HOLDOUT_END}.")
    print(f"Limit dzienny PRO: {status['limit_day']}; "
          f"uzycie przed audytem: {status['used_today']}; "
          "maks. 4 zapytania /fixtures.")
    for league_id, label, spec in SOURCES:
        # Pinned independent source is consulted, never saved or printed.
        raw = fetch_text(spec)
        train_source = read_openfootball_matches(raw, TRAIN_START, TRAIN_END)
        test_source = read_openfootball_matches(raw, HOLDOUT_START, HOLDOUT_END)
        train_api, skipped_train = api_window(league_id, TRAIN_START, TRAIN_END, key)
        test_api, skipped_test = api_window(league_id, HOLDOUT_START, HOLDOUT_END, key)
        result = score_holdout(train_source, train_api, test_source, test_api)
        metric_text = " ".join(f"{name}={count}" for name, count in result.items())
        print(f"{label}: {metric_text} "
              f"training_nonfinal={skipped_train} holdout_nonfinal={skipped_test}")
    print("Nie jest to backtest prognoz ani zatwierdzenie aliasow: "
          "snapshot archiwalny jest pozniejszy niz kontrolowane mecze.")
    print("Nie zapisano danych API, wynikow indywidualnych ani nazw klubow. "
          "Brak zmian w predictions.json, LAB, stronie i modelach.")


def main():
    try:
        run(os.environ.get("API_FOOTBALL_KEY", ""))
    except (OSError, ValueError, RuntimeError, UnicodeError) as exc:
        # Never leak a provider response or a team name through exception text.
        sys.exit(f"Test kontrolny: {type(exc).__name__}.")


if __name__ == "__main__":
    main()

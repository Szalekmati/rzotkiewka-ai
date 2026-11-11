"""RZOTKIEWKA: safe, aggregate-only identity checks for API-FOOTBALL team IDs.

Validates team IDs across /teams and two disjoint /fixtures windows.
Compares *proposed* OpenFootball name mappings to API roster entries only:
this cannot independently approve cross-provider club identity.
No team names, match details, or raw API records are written or logged.
"""
import os
import sys

from api_football_alias_candidates import propose_names
from api_football_crosscheck import (
    SOURCES, SEASON, clean_team, read_api_matches, read_openfootball_matches,
)
from api_football_holdout import (
    TRAIN_START, TRAIN_END, HOLDOUT_START, HOLDOUT_END, assert_windows,
)
from api_football_league_catalog import check_quota
from api_football_probe import api_get, verify_subscription
from api_football_fixtures_quality import utc_kickoff
from openfootball_history_audit import fetch_text

MAX_REQUESTS = 6
MAX_TEAMS = 150
MAX_FIXTURES = 100
MAX_NAMES = 500


def get_response(payload, maximum):
    if not isinstance(payload, dict) or type(payload.get("results")) is not int:
        raise RuntimeError("Odpowiedz nie zawiera wiarygodnego licznika.")
    items = payload.get("response")
    if not isinstance(items, list) or len(items) > maximum or len(items) != payload["results"]:
        raise RuntimeError("Brak kompletnej listy w odpowiedzi.")
    paging = payload.get("paging")
    if not isinstance(paging, dict) or paging.get("total") != 1:
        raise RuntimeError("Odpowiedz jest stronicowana lub niejednoznaczna.")
    return items


def valid_id(number):
    return type(number) is int and number > 0


def read_roster(payload):
    rows = get_response(payload, MAX_TEAMS)
    if not rows:
        raise RuntimeError("Pusty katalog druzyn.")
    by_id, by_name = {}, {}
    for item in rows:
        team = item.get("team") if isinstance(item, dict) else None
        if not isinstance(team, dict):
            raise RuntimeError("Brak poprawnego obiektu druzyny.")
        tid, name = team.get("id"), clean_team(team.get("name"))
        if not valid_id(tid) or not name or tid in by_id or name in by_name:
            raise RuntimeError("Brak ID lub niejednoznaczna nazwa/ID w katalogu.")
        by_id[tid] = name
        by_name[name] = tid
    return by_id, by_name


def fixture_ids(payload, league, season, start, end, roster):
    rows = get_response(payload, MAX_FIXTURES)
    seen, ids, misses, name_differences = set(), set(), 0, 0
    for item in rows:
        if not isinstance(item, dict):
            raise RuntimeError("Bledny rekord meczu.")
        fx, lg, teams = (item.get(k) for k in ("fixture", "league", "teams"))
        if not all(isinstance(x, dict) for x in (fx, lg, teams)):
            raise RuntimeError("Brak struktury meczu lub druzyn.")
        fid = fx.get("id")
        when = utc_kickoff(fx.get("date"))
        if (not valid_id(fid) or fid in seen or lg.get("id") != league or
                lg.get("season") != season or when is None or
                not start <= when.date() <= end):
            raise RuntimeError("Bledne ID lub sezon/data meczu.")
        seen.add(fid)
        home, away = teams.get("home"), teams.get("away")
        if not isinstance(home, dict) or not isinstance(away, dict):
            raise RuntimeError("Brak gospodarzy/gosci.")
        a,b = home.get("id"),away.get("id")
        if not valid_id(a) or not valid_id(b) or a == b:
            raise RuntimeError("Nieprawidlowe identyfikatory rywali.")
        for team in (home, away):
            tid = team["id"]
            name = clean_team(team.get("name"))
            if not name:
                raise RuntimeError("Pusta nazwa druzyny przy meczu.")
            ids.add(tid)
            if tid not in roster:
                misses += 1
            elif roster[tid] != name:
                name_differences += 1
    return {
        "fixture_count": len(rows),
        "distinct_fixture_team_ids": len(ids),
        "unknown_id_occurrences": misses,
        "roster_name_variations": name_differences,
        "team_ids": ids,
        "fixture_ids": seen,
    }


def inspect_identity(roster_payload, train_payload, test_payload, league_id,
                     source_train, start_train=TRAIN_START, end_train=TRAIN_END,
                     start_test=HOLDOUT_START, end_test=HOLDOUT_END):
    roster, name_to_id = read_roster(roster_payload)
    train_ids = fixture_ids(train_payload, league_id, SEASON, start_train, end_train, roster)
    test_ids = fixture_ids(test_payload, league_id, SEASON, start_test, end_test, roster)
    if train_ids["fixture_ids"] & test_ids["fixture_ids"]:
        raise RuntimeError("Ten sam mecz w rozdzielnych okresach.")
    # Reject *identity approval* whenever roster and fixture metadata conflict.
    if train_ids["unknown_id_occurrences"] or test_ids["unknown_id_occurrences"]:
        quality = "DO_WERYFIKACJI_ID"
    elif train_ids["roster_name_variations"] or test_ids["roster_name_variations"]:
        quality = "DO_WERYFIKACJI_NAZW"
    else:
        quality = "SPÓJNE_WEWNATRZ_API"
    api_train, _ = read_api_matches(train_payload, league_id, SEASON, start_train, end_train)
    source_names = {n for _, a, b, _ in source_train for n in (a, b)}
    api_names = {n for _, a, b, _ in api_train for n in (a, b)}
    proposals, _ = propose_names(source_names, api_names)
    # A name appears once in the API roster, or we do NOT link it to an ID.
    mapped = {source: name_to_id[api_name] for source, api_name in proposals.items()
              if api_name in name_to_id}
    return {
        "quality": quality,
        "roster_teams": len(roster),
        "train_fixtures": train_ids["fixture_count"],
        "test_fixtures": test_ids["fixture_count"],
        "distinct_ids_train": train_ids["distinct_fixture_team_ids"],
        "distinct_ids_test": test_ids["distinct_fixture_team_ids"],
        "shared_ids_across_windows": len(train_ids["team_ids"] & test_ids["team_ids"]),
        "unknown_ids_train": train_ids["unknown_id_occurrences"],
        "unknown_ids_test": test_ids["unknown_id_occurrences"],
        "name_variations_train": train_ids["roster_name_variations"],
        "name_variations_test": test_ids["roster_name_variations"],
        "alias_candidates": len(proposals),
        "candidates_linked_to_unique_api_id": len(mapped),
        "candidates_without_roster_id": len(proposals)-len(mapped),
        "APPROVED_FOR_PRODUCTION": False,
    }


def run(key):
    assert_windows(TRAIN_START, TRAIN_END, HOLDOUT_START, HOLDOUT_END)
    if MAX_REQUESTS != 3 * len(SOURCES):
        raise RuntimeError("Zly budzet audytu.")
    status = verify_subscription(api_get("status", key))
    check_quota(status, needed=MAX_REQUESTS, reserve=100)
    print("RZOTKIEWKA: badanie tozsamosci ID, bez publikacji danych i autoryzacji aliasow.")
    print(f"Plan PRO: limit {status['limit_day']}; uzycie przed: {status['used_today']}; "
          f"maks. {MAX_REQUESTS} zapytan z dziennego limitu.")
    for league_id, label, spec in SOURCES:
        source_text = fetch_text(spec)
        source_train = read_openfootball_matches(source_text, TRAIN_START, TRAIN_END)
        roster_payload = api_get("teams", key, {
            "league": str(league_id), "season": str(SEASON),
        })
        train_payload = api_get("fixtures", key, {
            "league": str(league_id), "season": str(SEASON),
            "from": TRAIN_START.isoformat(), "to": TRAIN_END.isoformat(),
            "timezone": "UTC",
        })
        test_payload = api_get("fixtures", key, {
            "league": str(league_id), "season": str(SEASON),
            "from": HOLDOUT_START.isoformat(), "to": HOLDOUT_END.isoformat(),
            "timezone": "UTC",
        })
        summary = inspect_identity(roster_payload, train_payload,
                                   test_payload, league_id, source_train)
        print(f"{label}: " + " ".join(f"{k}={v}" for k,v in summary.items()))
    print("To wewnetrzny test ID API, a NIE niezalezny dowod tozsamosci "
          "17 klubow OpenFootball. Zadna nowa liga ani alias nie zostal wdrozony.")


if __name__ == "__main__":
    try:
        run(os.environ.get("API_FOOTBALL_KEY", ""))
    except (RuntimeError, ValueError, OSError, UnicodeError) as exc:
        # No provider response, club identity or credential appears in errors.
        sys.exit(f"Audyt team ID: {type(exc).__name__}.")

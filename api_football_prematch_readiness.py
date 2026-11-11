"""Read-only API-FOOTBALL data-readiness audit for RZOTKIEWKA AI.

Never generates, saves or publishes a prediction. Separates *already ended*
fixtures from upcoming matches at an observed UTC time. It checks whether
the existing 2.1 Poisson engine would have enough PREVIOUS match results.
No API data, match names, predictions or team IDs are written to the repo.
"""
from datetime import datetime, timedelta, timezone
import json
import os
import sys

from api_football_probe import api_get, verify_subscription
from api_football_league_catalog import check_quota
from api_football_fixtures_quality import utc_kickoff
from club_identity_release_gate import DEFAULT_REGISTRY, inspect
from forecast_engine import (
    MIN_LEAD_HOURS, MAX_LEAD_DAYS, MIN_LEAGUE, MIN_TEAM,
    SETTLE_HOURS, prior_history, team_recent,
)

LEAGUES = ((39, "Premier League"), (140, "LaLiga"))
SEASON = 2026
MAX_ROWS = 500
RESERVE = 100
FINAL = {"FT", "AET"}
UPCOMING = {"NS", "TBD"}


def positive(value):
    return type(value) is int and value > 0


def parse_fixtures(payload, league, season):
    """Fail closed on duplicates, other leagues, bad timestamps and missing IDs."""
    if (not isinstance(payload, dict) or
            not isinstance(payload.get("response"), list) or
            type(payload.get("results")) is not int):
        raise ValueError("Nieprawidlowa struktura danych meczow.")
    rows = payload["response"]
    if len(rows) > MAX_ROWS or len(rows) != payload["results"]:
        raise ValueError("Za duzo rekordow lub bledny licznik.")
    paging = payload.get("paging")
    if not isinstance(paging, dict) or paging.get("total") != 1:
        raise ValueError("Paginacja nie pozwala weryfikowac pelnej listy.")
    normalized = []
    ids = set()
    discarded_status = 0
    incomplete_final = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Rekord meczu nie jest obiektem.")
        fixture, group, teams = (row.get(k) for k in ("fixture", "league", "teams"))
        if not all(isinstance(v, dict) for v in (fixture, group, teams)):
            raise ValueError("Brak struktury spotkania, ligi lub druzyn.")
        fid = fixture.get("id")
        date = utc_kickoff(fixture.get("date"))
        if (not positive(fid) or fid in ids or date is None
                or group.get("id") != league or group.get("season") != season):
            raise ValueError("Duplikat ID, bledna data, liga lub sezon.")
        ids.add(fid)
        home, away = teams.get("home"), teams.get("away")
        if not isinstance(home, dict) or not isinstance(away, dict):
            raise ValueError("Brak zespolow.")
        hid, aid = home.get("id"), away.get("id")
        if not positive(hid) or not positive(aid) or hid == aid:
            raise ValueError("Niepoprawne ID rywali.")
        for team in (home, away):
            if not isinstance(team.get("name"), str) or not team["name"].strip():
                raise ValueError("Brak nazwy zespolu.")
        status = fixture.get("status")
        short = status.get("short") if isinstance(status, dict) else None
        if not isinstance(short, str):
            raise ValueError("Brak statusu meczu.")
        score = None
        if short in FINAL:
            goals = row.get("goals")
            if (not isinstance(goals, dict) or
                    any(type(goals.get(side)) is not int or
                        not 0 <= goals[side] <= 30 for side in ("home", "away"))):
                incomplete_final += 1
            else:
                score = [goals["home"], goals["away"]]
        elif short not in UPCOMING:
            discarded_status += 1
        normalized.append({
            "id": fid, "kickoff": date, "home_id": hid, "away_id": aid,
            "score": score, "status": short,
        })
    return normalized, {"discarded_other_status": discarded_status,
                        "incomplete_final": incomplete_final}


def inspect_asof(matches, now):
    """Report availability only, and never compute probabilities or game tips."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Snapshot musi miec strefe UTC.")
    now = now.astimezone(timezone.utc)
    historical = [m for m in matches
                  if m["status"] in FINAL and m["score"] is not None
                  and m["kickoff"] <= now - timedelta(hours=SETTLE_HOURS)]
    future = [m for m in matches
              if m["status"] in UPCOMING and m["score"] is None
              and m["kickoff"] > now]
    possible = [
        m for m in future
        if now + timedelta(hours=MIN_LEAD_HOURS) < m["kickoff"]
        <= now + timedelta(days=MAX_LEAD_DAYS)
    ]
    ready = missing_history = 0
    for m in possible:
        # Uses the real engine's strict pre-match historical cutoff.
        past = prior_history(historical, m["kickoff"], now)
        own = team_recent(past, m["home_id"])
        opponents = team_recent(past, m["away_id"])
        if len(past) >= MIN_LEAGUE and min(len(own), len(opponents)) >= MIN_TEAM:
            ready += 1
        else:
            missing_history += 1
    # Finished games with future kickoff would imply impossible metadata.
    bad_chronology = sum(
        m["status"] in FINAL and m["kickoff"] > now for m in matches
    )
    return {
        "fixture_records": len(matches),
        "past_completed_settled": len(historical),
        "future_scheduled": len(future),
        "possible_window": len(possible),
        "enough_history_in_window": ready,
        "not_enough_history_in_window": missing_history,
        "finished_kickoff_after_snapshot": bad_chronology,
        "forecast_records_written": 0,
    }


def run(key):
    # This does NOT authorize any cross-provider map or release.
    registry = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    if inspect(registry)["production_release_allowed"]:
        raise RuntimeError("Badawczy adapter wymaga zablokowanego wdrozenia.")
    status = verify_subscription(api_get("status", key))
    check_quota(status, needed=len(LEAGUES), reserve=RESERVE)
    now = datetime.now(timezone.utc)
    print(f"RZOTKIEWKA DATA READINESS: {now.isoformat(timespec='seconds')}, "
          f"sezon {SEASON}; limit PRO: {status['limit_day']}, "
          f"wykorzystano przed: {status['used_today']}; max 2 odczyty /fixtures.")
    for league, label in LEAGUES:
        data = api_get("fixtures", key, {"league": str(league), "season": str(SEASON)})
        games, quality = parse_fixtures(data, league, SEASON)
        stats = inspect_asof(games, now)
        verdict = ("DO_WERYFIKACJI" if quality["incomplete_final"] or
                   stats["finished_kickoff_after_snapshot"] else
                   "BRAK_MECZOW_W_OKNIE" if not stats["possible_window"] else
                   "HISTORIA_NIEWYSTARCZAJACA" if not stats["enough_history_in_window"] else
                   "DANE_WYSTARCZAJA_DO_BADANIA")
        print(f"{label}: {verdict}; " +
              " ".join(f"{k}={v}" for k, v in {**quality, **stats}.items()))
    print("To nie sa prognozy: zero prawdopodobienstw, brak zmian LAB/archiwum. "
          "Wdrozenie nowych lig nadal zablokowane przez oddzielna bramke.")


if __name__ == "__main__":
    try:
        run(os.environ.get("API_FOOTBALL_KEY", ""))
    except (OSError, RuntimeError, ValueError, TypeError, KeyError) as exc:
        sys.exit(f"Readiness: {type(exc).__name__}.")

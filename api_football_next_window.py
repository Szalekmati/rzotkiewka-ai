"""Read-only schedule of next possible RZOTKIEWKA research window.

No new predictions, no team names or IDs in logs, no provider data saved.
The candidate window describes WHEN a fixture enters the CURRENT model's
2-hour..8-day timing filter; it does NOT mean the data/model is approved.
"""
from datetime import datetime, timedelta, timezone
import json
import os
import sys
from zoneinfo import ZoneInfo

from api_football_prematch_readiness import (
    LEAGUES, SEASON, RESERVE, UPCOMING, parse_fixtures, inspect_asof,
)
from api_football_probe import api_get, verify_subscription
from api_football_league_catalog import check_quota
from club_identity_release_gate import DEFAULT_REGISTRY, inspect
from forecast_engine import MIN_LEAD_HOURS, MAX_LEAD_DAYS

WARSAW = ZoneInfo("Europe/Warsaw")


def display_time(dt):
    if dt is None:
        return "BRAK"
    return dt.astimezone(timezone.utc).isoformat(timespec="minutes") + " | PL: " + (
        dt.astimezone(WARSAW).strftime("%Y-%m-%d %H:%M %Z"))


def window_summary(rows, now):
    """UTC safe; active filter (2h,8d], next opening if after current time.

    The opening is inclusive and closing exclusive, mirroring the 2.1
    forecast_engine condition now + 2h < kickoff <= now + 8 days.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Wymagany czas ze strefa.")
    now = now.astimezone(timezone.utc)
    planned = sorted((g for g in rows
                      if g["status"] in UPCOMING and g["score"] is None
                      and g["kickoff"] > now),
                     key=lambda g: g["kickoff"])
    windows = []
    for g in planned:
        kickoff = g["kickoff"]
        opening = kickoff - timedelta(days=MAX_LEAD_DAYS)
        closing = kickoff - timedelta(hours=MIN_LEAD_HOURS)
        if closing <= now:
            continue
        windows.append((opening, closing, kickoff))
    active = [(a, b, c) for a,b,c in windows if a <= now < b]
    future = [(a, b, c) for a,b,c in windows if a > now]
    nearest_future = min(future, key=lambda x:(x[0],x[2])) if future else None
    first_active = min(active, key=lambda x:x[2]) if active else None
    earliest_kickoff = planned[0]["kickoff"] if planned else None
    return {
        "scheduled_future": len(planned),
        "windows_currently_active": len(active),
        "windows_to_open_later": len(future),
        "nearest_kickoff": earliest_kickoff,
        "first_current_window_kickoff": first_active[2] if first_active else None,
        "next_open": nearest_future[0] if nearest_future else None,
        "next_close": nearest_future[1] if nearest_future else None,
        "next_window_kickoff": nearest_future[2] if nearest_future else None,
    }


def run(key):
    registry = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    if inspect(registry)["production_release_allowed"]:
        raise RuntimeError("Brak izolacji produkcyjnej badania.")
    status = verify_subscription(api_get("status", key))
    check_quota(status, needed=len(LEAGUES), reserve=RESERVE)
    now = datetime.now(timezone.utc)
    print(f"RZOTKIEWKA next window, punkt kontrolny: {display_time(now)}.")
    print(f"PRO aktywny: limit {status['limit_day']}, uzyte przed {status['used_today']}; "
          "maksymalnie 2 odczyty /fixtures, bez automatu i nowych zakupow.")
    for league, label in LEAGUES:
        provider = api_get("fixtures", key, {
            "league": str(league), "season": str(SEASON)})
        fixtures, quality = parse_fixtures(provider, league, SEASON)
        current = inspect_asof(fixtures, now)
        future = window_summary(fixtures, now)
        if quality["incomplete_final"] or current["finished_kickoff_after_snapshot"]:
            state = "DO_WERYFIKACJI"
        elif future["windows_currently_active"]:
            state = "AKTYWNE_OKNO_BADAWCZE"
        elif future["next_open"]:
            state = "NASTEPNE_OKNO_ZAPLANOWANE"
        else:
            state = "BRAK_OKNA_W_ODPOWIEDZI"
        print(f"{label}: {state}; "
              f"przyszle={future['scheduled_future']} "
              f"okna_aktywne={future['windows_currently_active']} "
              f"okna_przyszle={future['windows_to_open_later']} "
              f"do_dalszego_badania_w_aktywnym_oknie={current['enough_history_in_window']}")
        print(f"{label} najblizszy start: {display_time(future['nearest_kickoff'])}")
        print(f"{label} przyszle otwarcie okna: {display_time(future['next_open'])}")
        print(f"{label} zamkniecie tego okna (nie wlacznie): {display_time(future['next_close'])}")
        print(f"{label} kickoff dla kolejnego okna: {display_time(future['next_window_kickoff'])}")
    print("UWAGA: Terminarze moga sie zmienic. Nalezy ponowic weryfikacje "
          "w samym oknie; wyniki i aliasy nie sa zatwierdzone do prognoz. "
          "Zero opublikowanych lub zapisanych nowych prognoz.")


if __name__ == "__main__":
    try:
        run(os.environ.get("API_FOOTBALL_KEY", ""))
    except (OSError, RuntimeError, ValueError, TypeError, KeyError) as exc:
        sys.exit(f"RZOTKIEWKA next window: {type(exc).__name__}.")

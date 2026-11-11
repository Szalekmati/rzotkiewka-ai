"""Kontrolowany, tylko-do-odczytu test API-FOOTBALL PRO.

Nie zapisuje pobranych danych ani klucza; nie zmienia modelu i archiwum.
"""
import argparse
from datetime import date, datetime, timezone
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://v3.football.api-sports.io"
MAX_BYTES = 5_000_000


def api_get(endpoint, key, params=None, opener=None):
    if not key or not key.strip():
        raise ValueError("Brak API_FOOTBALL_KEY w GitHub Secrets.")
    if opener is None:
        opener = urllib.request.urlopen
    query = urllib.parse.urlencode(params or {})
    url = BASE + "/" + endpoint + (("?" + query) if query else "")
    req = urllib.request.Request(url, headers={"x-apisports-key": key.strip()}, method="GET")
    try:
        with opener(req, timeout=20) as response:
            payload = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"API zwrocilo HTTP {err.code}.") from None
    except urllib.error.URLError:
        raise RuntimeError("Brak lacznosci z API-FOOTBALL.") from None
    if len(payload) > MAX_BYTES:
        raise RuntimeError("Odpowiedz jest zbyt duza; dane nie sa publikowane.")
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        raise RuntimeError("Nieprawidlowa odpowiedz JSON.") from None
    if not isinstance(data, dict) or data.get("errors"):
        # Nie wypisujemy surowych bledow dostawcy ani danych konta.
        raise RuntimeError("API odrzucilo zapytanie lub zwrocilo blad.")
    return data


def verify_subscription(data):
    account = data.get("response")
    if not isinstance(account, dict):
        raise RuntimeError("Brak struktury statusu subskrypcji.")
    sub = account.get("subscription")
    usage = account.get("requests")
    if not isinstance(sub, dict) or not isinstance(usage, dict):
        raise RuntimeError("Brak danych planu lub limitu.")
    plan = str(sub.get("plan", "nieznany"))
    active = sub.get("active") is True
    daily = usage.get("limit_day")
    current = usage.get("current")
    if not isinstance(daily, int) or isinstance(daily, bool):
        raise RuntimeError("Brak wiarygodnego limitu dziennego.")
    if not isinstance(current, int) or isinstance(current, bool):
        raise RuntimeError("Brak wiarygodnego licznika zapytan.")
    if not active or daily < 7500:
        raise RuntimeError("Pakiet PRO nie zostal potwierdzony jako aktywny.")
    # Nigdy nie logujemy prywatnych pol: account/email/name ani klucza.
    return {"plan": plan, "limit_day": daily, "used_today": current}


def fixture_query(league, season, day):
    if not league.isdecimal() or not 1 <= int(league) <= 999999:
        raise ValueError("Nieprawidlowy numer ligi.")
    if not season.isdecimal() or len(season) != 4:
        raise ValueError("Nieprawidlowy sezon.")
    try:
        day = date.fromisoformat(day).isoformat()
    except ValueError:
        raise ValueError("Data musi miec format RRRR-MM-DD.") from None
    return {"league": str(int(league)), "season": season, "date": day}


def main():
    p = argparse.ArgumentParser(description="Tylko odczyt: status i probka terminarza")
    p.add_argument("--mode", choices=("status", "fixtures"), default="status")
    p.add_argument("--league", default="39")
    p.add_argument("--season", default="2026")
    p.add_argument("--date", default="")
    args = p.parse_args()
    key = os.environ.get("API_FOOTBALL_KEY", "")
    try:
        status = verify_subscription(api_get("status", key))
        print("Polaczenie API-FOOTBALL: OK")
        print(f"Plan: {status['plan']}; dzienny limit: {status['limit_day']}; wykorzystano: {status['used_today']}")
        if args.mode == "fixtures":
            day = args.date or datetime.now(timezone.utc).date().isoformat()
            params = fixture_query(args.league, args.season, day)
            data = api_get("fixtures", key, params)
            count = data.get("results")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise RuntimeError("API nie zwrocilo prawidlowej liczby meczow.")
            print(f"Proba terminarza: liga {params['league']}, sezon {params['season']}, dzien {params['date']}; liczba spotkan: {count}")
            print("Dane meczowe nie zostaly zapisane ani opublikowane.")
    except (RuntimeError, ValueError) as err:
        p.exit(1, f"Test API-FOOTBALL: {err}\n")


if __name__ == "__main__":
    main()

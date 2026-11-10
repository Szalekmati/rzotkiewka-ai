#!/usr/bin/env python3
"""Read-only quality audit of candidate leagues. Never produces 1X2 forecasts.

A positive result means 'worth manual review', NOT approved for production.
No commits, changes to predictions.json, training, bets or model promotion.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://api.openligadb.de/getmatchdata"
CANDIDATES = {
    "pl": "Premier League (Anglia)",
    "la1": "LaLiga (Hiszpania)",
    "ucl": "Liga Mistrzów UEFA",
}
TIMEOUT_SECONDS = 18
MIN_FIXTURES = 60
MIN_HISTORICAL_RESULTS = 50
MIN_CURRENT_RESULTS = 10
MIN_FUTURE_FIXTURES = 1
MIN_VALID_FRACTION = 0.98
OUT = Path("league_audit")


def parse_utc(raw):
    text = raw.get("matchDateTimeUTC")
    if not isinstance(text, str) or not text:
        return None
    try:
        date = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        date = date.astimezone(timezone.utc)
        if not 2000 <= date.year <= 2100:
            return None
        return date
    except (ValueError, TypeError, OverflowError):
        return None


def accepted_final_score(raw):
    if raw.get("matchIsFinished") is not True:
        return None
    results = raw.get("matchResults")
    if not isinstance(results, list):
        return None
    for item in results:
        if not isinstance(item, dict):
            continue
        if item.get("resultTypeID") != 2 and "endergebnis" not in str(item.get("resultName", "")).lower():
            continue
        a, b = item.get("pointsTeam1"), item.get("pointsTeam2")
        if type(a) is int and type(b) is int and 0 <= a <= 40 and 0 <= b <= 40:
            return [a, b]
    return None


def normalize(raw):
    if not isinstance(raw, dict):
        return None
    home, away = raw.get("team1"), raw.get("team2")
    if not isinstance(home, dict) or not isinstance(away, dict):
        return None
    mids = [raw.get("matchID"), home.get("teamId"), away.get("teamId")]
    if not all(type(x) is int and x > 0 for x in mids):
        return None
    if mids[1] == mids[2]:
        return None
    if not all(isinstance(team.get("teamName"), str) and team["teamName"].strip() for team in (home, away)):
        return None
    date = parse_utc(raw)
    if date is None:
        return None
    return {
        "id": mids[0], "kickoff": date,
        "finished_flag": raw.get("matchIsFinished") is True,
        "score": accepted_final_score(raw),
    }


def assess(raw_matches, now):
    """Return data-quality signals only; do not estimate outcome probabilities."""
    if not isinstance(raw_matches, list):
        raise ValueError("API response is not a match array")
    valid = [item for raw in raw_matches if (item := normalize(raw)) is not None]
    unique_ids = {m["id"] for m in valid}
    future = [m for m in valid if m["kickoff"] > now and not m["finished_flag"]]
    settled = [m for m in valid if m["score"] is not None and m["kickoff"] <= now]
    invalid_finished = sum(m["finished_flag"] and m["score"] is None for m in valid)
    # Pomijamy 48 h na rozpoczęcie i aktualizację wyniku.
    overdue_without_result = sum(m["kickoff"] <= now - timedelta(hours=48)
                                 and m["score"] is None for m in valid)
    return {
        "total": len(raw_matches),
        "valid": len(valid),
        "valid_fraction": round(len(valid) / len(raw_matches), 4) if raw_matches else 0.0,
        "duplicate_ids": len(valid) - len(unique_ids),
        "finished_with_score": len(settled),
        "finished_without_accepted_score": invalid_finished,
        "overdue_without_result_48h": overdue_without_result,
        "future_with_kickoff": len(future),
        "nearest_future_utc": min((m["kickoff"].isoformat() for m in future), default=None),
    }


def verdict(historical, current):
    reasons = []
    for season_type, block in (("poprzedni", historical), ("bieżący", current)):
        if block.get("error"):
            reasons.append("Błąd API (" + season_type + " sezon)")
            continue
        if block["total"] < MIN_FIXTURES:
            reasons.append("Za mało meczów (" + season_type + " sezon)")
        if block["valid_fraction"] < MIN_VALID_FRACTION:
            reasons.append("Niekompletne identyfikatory/datowanie (" + season_type + " sezon)")
        if block["duplicate_ids"]:
            reasons.append("Powtórzone identyfikatory (" + season_type + " sezon)")
        if block["finished_without_accepted_score"]:
            reasons.append("Zamknięte mecze bez potwierdzonego wyniku (" + season_type + " sezon)")
        if block["overdue_without_result_48h"]:
            reasons.append("Zaległe mecze >48h bez wyniku (" + season_type + " sezon)")
    if not historical.get("error") and historical["finished_with_score"] < MIN_HISTORICAL_RESULTS:
        reasons.append("Za mało historycznych wyników końcowych")
    if not current.get("error"):
        if current["finished_with_score"] < MIN_CURRENT_RESULTS:
            reasons.append("Za mało wyników bieżącego sezonu")
        if current["future_with_kickoff"] < MIN_FUTURE_FIXTURES:
            reasons.append("Brak przyszłych terminów")
    return ("DO RĘCZNEJ OCENY", []) if not reasons else ("DANE NIEWYSTARCZAJĄCE", reasons)


def get_matches(code, season):
    url = API + "/" + code + "/" + str(season)
    request = Request(url, headers={"User-Agent": "RZOTKIEWKA-AI-readonly-audit/1.0",
                                    "Accept": "application/json"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise ValueError("HTTP " + str(response.status))
        data = response.read(8_000_001)
    if len(data) > 8_000_000:
        raise ValueError("Response exceeds 8 MB safety limit")
    return json.loads(data)


def run(now=None, output=OUT):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Audit time must be timezone-aware")
    season = now.year if now.month >= 7 else now.year - 1
    records = []
    for code, label in CANDIDATES.items():
        datasets = []
        for year in (season - 1, season):
            try:
                data = get_matches(code, year)
                item = assess(data, now)
            except (HTTPError, URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
                item = {"error": str(exc)[:160]}
            item["season"] = year
            datasets.append(item)
        decision, reasons = verdict(*datasets)
        records.append({"shortcut": code, "league": label, "decision": decision,
                        "reasons": reasons, "historical": datasets[0], "current": datasets[1]})
    document = {
        "kind": "read_only_league_candidate_audit",
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "source": API,
        "thresholds": {
            "min_fixtures": MIN_FIXTURES,
            "min_historical_results": MIN_HISTORICAL_RESULTS,
            "min_current_results": MIN_CURRENT_RESULTS,
            "min_future_fixtures": MIN_FUTURE_FIXTURES,
            "min_valid_fraction": MIN_VALID_FRACTION,
        },
        "automatic_promotion": False,
        "candidates": records,
    }
    lines = [
        "# RZOTKIEWKA — audyt nowych lig (bez prognoz)",
        "",
        "Kontrola UTC: " + document["observed_at_utc"],
        "",
        "Źródło: OpenLigaDB. Wyniki społecznościowe mogą być opóźnione lub niepełne.",
        "**Status DO RĘCZNEJ OCENY nie oznacza dopuszczenia ligi do aplikacji ani LAB.**",
        "Brak zmian w modelach, predykcjach, prognozach i dostępie Premium.",
        "",
        "| Rozgrywki | Historia: wyniki | Sezon: mecze | Sezon: wyniki | Przyszłe | Ocena |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in records:
        hist, cur = item["historical"], item["current"]
        met = lambda block, name: str(block.get(name, "—"))
        lines.append("| " + item["league"] + " | " +
                     met(hist, "finished_with_score") + " | " +
                     met(cur, "total") + " | " +
                     met(cur, "finished_with_score") + " | " +
                     met(cur, "future_with_kickoff") + " | " +
                     item["decision"] + " |")
        if item["reasons"]:
            lines.append("")
            lines.append("**" + item["league"] + ":** " + "; ".join(item["reasons"]) + ".")
            lines.append("")
        for block in (hist, cur):
            if block.get("error"):
                lines.append("API " + item["shortcut"] + "/" + str(block["season"]) +
                             ": " + block["error"] + ".")
    lines += [
        "",
        "Kryteria są progami wstępnymi, nie dowodem kompletności każdej kolejki.",
        "Przed dodaniem ligi wymagane: kontrola mecz po meczu, opóźnień wyników,",
        "historycznych sezonów, licencji i sprawdzenie rozbieżności z niezależnym źródłem.",
        "Silnik LAB 2.1/2.2 i sezonowe archiwum pozostają bez zmian.",
        "",
    ]
    output.mkdir(parents=True, exist_ok=True)
    (output / "RAPORT_LIG.md").write_text("\n".join(lines), encoding="utf-8")
    (output / "wyniki_lig.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
    return document


if __name__ == "__main__":
    run()

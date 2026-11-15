#!/usr/bin/env python3
"""Read-only overview of the frozen RZOTKIEWKA LAB 2.1/2.2 ledger.

Does not call APIs, modify files, grade fixtures, promote models, or infer ROI.
A ledger status is not an independent verification of a match result.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Brak lub niepoprawny znacznik czasu")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Niepoprawny znacznik czasu") from exc
    if parsed.tzinfo is None:
        raise ValueError("Znacznik czasu musi zawierac strefe")
    return parsed.astimezone(timezone.utc)


def summary(ledger, experiment, *, now):
    """Validate structure; count statuses only, without estimating accuracy."""
    if not isinstance(ledger, dict) or ledger.get("schema") != 1:
        raise ValueError("Nieznana wersja dziennika LAB")
    if not isinstance(experiment, dict) or not isinstance(experiment.get("config"), dict):
        raise ValueError("Brak konfiguracji eksperymentu")
    threshold = experiment["config"].get("review_after_settled_pairs")
    if type(threshold) is not int or threshold < 1:
        raise ValueError("Brak dodatniego progu przegladu")
    items, observations = ledger.get("forecasts"), ledger.get("settlements")
    if not isinstance(items, list) or not isinstance(observations, dict):
        raise ValueError("Niepoprawna struktura dziennika")
    current = _timestamp(now) if isinstance(now, str) else now
    if not isinstance(current, datetime) or current.tzinfo is None:
        raise ValueError("Niepoprawny czas porownania")
    current = current.astimezone(timezone.utc)
    ids, counts, state_counts, next_kickoffs = set(), Counter(), Counter(), []
    for row in items:
        if not isinstance(row, dict) or not isinstance(row.get("snapshot"), dict):
            raise ValueError("Niepoprawna prognoza")
        ident, snap = row.get("id"), row["snapshot"]
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError("Brak lub powtorzony identyfikator prognozy")
        ids.add(ident)
        league, fixture = snap.get("league"), snap.get("fixture")
        if not isinstance(league, str) or not league or not isinstance(fixture, dict):
            raise ValueError("Brak danych ligi lub meczu")
        start = _timestamp(fixture.get("kickoff"))
        saved = _timestamp(snap.get("created_at"))
        if saved >= start:
            raise ValueError("Prognoza nie zostala zapisana przed meczem")
        counts[league] += 1
        if start > current:
            next_kickoffs.append(start)
        history = observations.get(ident, [])
        if not isinstance(history, list):
            raise ValueError("Niepoprawna historia rozliczen")
        if not history:
            state_counts["brak_obserwacji"] += 1
            continue
        versions = []
        for item in history:
            if not isinstance(item, dict) or not isinstance(item.get("result"), dict):
                raise ValueError("Niepoprawna obserwacja rozliczenia")
            state = item["result"].get("state")
            if not isinstance(state, str) or not state.strip():
                raise ValueError("Brak stanu rozliczenia")
            versions.append((_timestamp(item.get("observed_at")), state))
        # A later correction supersedes an earlier observation, never vice versa.
        state_counts[max(versions, key=lambda pair: pair[0])[1]] += 1
    if set(observations).difference(ids):
        raise ValueError("Rozliczenie bez odpowiadajacej prognozy")
    graded = state_counts.get("graded", 0)
    return {
        "pairs": len(items), "graded": graded, "by_league": dict(sorted(counts.items())),
        "states": dict(sorted(state_counts.items())), "threshold": threshold,
        "remaining": max(0, threshold - graded),
        "next_kickoff": min(next_kickoffs) if next_kickoffs else None,
    }


def format_report(data):
    lines = [
        "RZOTKIEWKA AI — informacyjny podglad LAB 2.1/2.2 (read-only)",
        f"Zapisane pary prognoz: {data['pairs']}",
        "Ligi: " + (", ".join(f"{k}: {v}" for k, v in data["by_league"].items()) or "brak"),
        "Ostatnie stany rozliczen: " + (
            ", ".join(f"{k}: {v}" for k, v in data["states"].items()) or "brak"),
        f"Wpisy ze stanem graded: {data['graded']}",
        f"Przeglad dopiero po {data['threshold']} rozliczonych parach; brakujace: {data['remaining']}",
    ]
    if data["next_kickoff"]:
        start = data["next_kickoff"].astimezone(ZoneInfo("Europe/Warsaw"))
        lines.append("Najblizszy przyszly kickoff wg zapisanego dziennika: "
                     + start.strftime("%Y-%m-%d %H:%M %Z"))
    else:
        lines.append("Brak przyszlych kickoffow w zapisanym dzienniku")
    lines += [
        "To odczyt historycznego stanu plikow, nie podglad biezacego API.",
        "Nie weryfikuje oficjalnych wynikow, SHA-256 ani skutecznosci modeli.",
        "Brak automatycznej promocji do Premium, typow ani transakcji.",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=ROOT / "lab_forward/ledger.json")
    parser.add_argument("--experiment", type=Path, default=ROOT / "lab_forward/experiment.json")
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        experiment = json.loads(args.experiment.read_text(encoding="utf-8"))
        print(format_report(summary(ledger, experiment, now=datetime.now(timezone.utc))))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"STOP: Nie mozna wiarygodnie odczytac dziennika LAB: {exc}\n")


if __name__ == "__main__":
    main()

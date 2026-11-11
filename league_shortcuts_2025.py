#!/usr/bin/env python3
"""Read-only OpenLigaDB season inventory. No models, forecasts or auto-admission.

Checks if the league shortcuts used by the candidate audit were even listed
for the historical 2025/26 season. Possible similarly named leagues are
manual leads ONLY: they are never substituted into production.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINT = "https://api.openligadb.de/getavailableleagues/2025"
OUTPUT = Path("league_audit")
LIMIT_BYTES = 2_000_000
TARGETS = ("pl", "la1")
# Loose name patterns produce REVIEW LEADS, NOT validated competition aliases.
NAME_HINTS = (
    "premier league", "english premier", "premiership",
    "la liga", "laliga", "liga espanola", "spanish primera",
    "spanische primera", "primera division",
)


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFKD", str(value).lower())
                   if not unicodedata.combining(c)).strip()


def safe_label(value):
    return re.sub(r"[\r\n|<>\[\]]+", " ", str(value)).strip()[:130]


def candidate_records(raw):
    if not isinstance(raw, list):
        raise ValueError("Available-leagues API must return a JSON array")
    if len(raw) > 50_000:
        raise ValueError("Too many league entries")
    rows = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        code, name = item.get("leagueShortcut"), item.get("leagueName")
        if not isinstance(code, str) or not code.strip():
            continue
        if not isinstance(name, str):
            name = ""
        season = str(item.get("leagueSeason", ""))
        norm_name = normalized(name)
        code = code.strip()
        exact = code.lower() in TARGETS
        hint = any(phrase in norm_name for phrase in NAME_HINTS)
        if not exact and not hint:
            continue
        key = (code.lower(), name, season)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "shortcut": code, "name": safe_label(name),
            "season": safe_label(season),
            "exact_old_shortcut": exact,
            "why_listed": "tested_shortcut" if exact else "name_similarity_only",
        })
    rows.sort(key=lambda r: (not r["exact_old_shortcut"], r["shortcut"].lower(), r["name"]))
    return {
        "source_entries": len(raw),
        "listed_shortcuts": {code: any(r["shortcut"].lower() == code for r in rows)
                             for code in TARGETS},
        "manual_review_leads": rows[:75],
        "matching_entries": len(rows),
        "truncated_leads": len(rows) > 75,
        "automatic_promotion": False,
    }


def fetch_inventory():
    request = Request(ENDPOINT, headers={
        "User-Agent": "RZOTKIEWKA-AI-readonly-source-research/1.0",
        "Accept": "application/json",
    })
    with urlopen(request, timeout=18) as response:
        if response.status != 200:
            raise ValueError("Unexpected API HTTP status: " + str(response.status))
        blob = response.read(LIMIT_BYTES + 1)
    if len(blob) > LIMIT_BYTES:
        raise ValueError("API inventory exceeds 2 MB safe limit")
    return json.loads(blob)


def run(output=OUTPUT, at=None):
    at = at or datetime.now(timezone.utc)
    if at.tzinfo is None:
        raise ValueError("Audit timestamp must have timezone")
    doc = {
        "kind": "historical_league_shortcut_inventory_only",
        "source": ENDPOINT,
        "checked_at_utc": at.astimezone(timezone.utc).isoformat(),
        "season": "2025",
        "automatic_promotion": False,
    }
    try:
        doc.update(candidate_records(fetch_inventory()))
        doc["fetch_ok"] = True
    except (HTTPError, URLError, TimeoutError, ValueError,
            OSError, json.JSONDecodeError) as error:
        doc["fetch_ok"] = False
        doc["error"] = type(error).__name__ + ": " + str(error)[:160]
    lines = [
        "# RZOTKIEWKA — wykaz skrótów lig na sezon 2025/26",
        "",
        "Odczyt UTC: " + doc["checked_at_utc"],
        "Endpoint: " + ENDPOINT,
        "To osobny odczyt listy lig, NIE wyników spotkań.",
        "Podobieństwo nazwy ani obecność skrótu nie potwierdza danych historycznych.",
        "**BRAK automatycznej zmiany identyfikatorów, prognoz lub silników.**",
        "",
    ]
    if not doc["fetch_ok"]:
        lines += ["Nie udało się potwierdzić wykazu lig: " + doc["error"],
                  "Nie można na tej podstawie orzekać o dostępności historii.", ""]
    else:
        lines += [
            "Liczba wpisów źródła: " + str(doc["source_entries"]),
            "Zbadane skróty: " + ", ".join(
                code + (" — NA LIŚCIE" if present else " — BRAK NA LIŚCIE")
                for code, present in doc["listed_shortcuts"].items()
            ),
            "Potencjalne podobieństwa nazw (ręczna ocena, brak automatycznego dopasowania):",
            "",
            "| Skrót | Nazwa w źródle | Sezon | Powód wskazania |",
            "|---|---|---|---|",
        ]
        for row in doc["manual_review_leads"]:
            lines.append("| " + row["shortcut"] + " | " + row["name"] +
                         " | " + row["season"] + " | " + row["why_listed"] + " |")
        if not doc["manual_review_leads"]:
            lines.append("| — | Brak pasujących rekordów w tej odpowiedzi | — | — |")
        if doc["truncated_leads"]:
            lines.append("**Uwaga:** próbka ograniczona do 75 nazw; nie jest wyczerpująca.")
        lines += ["", "Następny krok: potwierdzić niezależnie tożsamość każdej ligi,",
                  "kompletność historycznych wyników, prawa do danych i zgodność terminów.",
                  "Brak skrótu na liście nie przesądza, że liga nie istnieje.", ""]
    output.mkdir(parents=True, exist_ok=True)
    (output / "SKROTY_LIG_2025.md").write_text("\n".join(lines), encoding="utf-8")
    (output / "skroty_lig_2025.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
    return doc


if __name__ == "__main__":
    run()

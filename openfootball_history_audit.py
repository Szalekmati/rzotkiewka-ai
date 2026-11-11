#!/usr/bin/env python3
"""Read-only structural audit of OpenFootball 2025/26 results (not a model input).

All sources are pinned to reviewed Git commit hashes. A passing result means
the two text files are internally consistent, NOT that each result, fixture
time or license provenance has been independently validated.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUTPUT = Path("league_audit")
SOURCES = {
    "Premier League": {
        "repo": "openfootball/england",
        "commit": "9ee7a0c351805c99cc334478a9bf04b7d0432fec",
        "path": "2025-26/1-premierleague.txt",
    },
    "LaLiga": {
        "repo": "openfootball/espana",
        "commit": "80035a93dd4920985af52aa097a54a6fb888563b",
        "path": "2025-26/1-liga.txt",
    },
}
LIMIT_BYTES = 450_000
TIMED = re.compile(r"^[ \t]*\d{1,2}:\d{2}[ \t]+")
SCORE = re.compile(
    r"^[ \t]*(?P<clock>\d{1,2}:\d{2})[ \t]+"
    r"(?P<home>.+?)[ \t]{2,}(?P<home_score>\d{1,2})-"
    r"(?P<away_score>\d{1,2})[ \t]+"
    r"\((?P<half_home>\d{1,2})-(?P<half_away>\d{1,2})\)"
    r"[ \t]+(?P<away>.+?)[ \t]*$"
)
DECLARED = re.compile(r"^# Matches[ \t]+(\d+)[ \t]*$", re.MULTILINE)
DECLARED_TEAMS = re.compile(r"^# Teams[ \t]+(\d+)[ \t]*$", re.MULTILINE)


def source_url(spec):
    return ("https://raw.githubusercontent.com/" + spec["repo"] + "/" +
            spec["commit"] + "/" + spec["path"])


def fetch_text(spec):
    url = source_url(spec)
    req = Request(url, headers={"Accept": "text/plain",
                                 "User-Agent": "RZOTKIEWKA-CC0-readonly-research/1.0"})
    with urlopen(req, timeout=18) as resp:
        if resp.status != 200:
            raise ValueError("Source returned HTTP " + str(resp.status))
        data = resp.read(LIMIT_BYTES + 1)
    if len(data) > LIMIT_BYTES:
        raise ValueError("Source file exceeds 450 KB")
    return data.decode("utf-8-sig")


def assess_text(text, *, expected_matches=380, expected_teams=20):
    if not isinstance(text, str):
        raise ValueError("Expected Football.TXT text")
    matches = []
    invalid = []
    for line in text.splitlines():
        if not TIMED.match(line):
            continue
        m = SCORE.fullmatch(line)
        if not m:
            invalid.append("unparsable")
            continue
        row = m.groupdict()
        a, b = row["home"].strip(), row["away"].strip()
        s1, s2 = int(row["home_score"]), int(row["away_score"])
        h1, h2 = int(row["half_home"]), int(row["half_away"])
        hours, minutes = (int(x) for x in row["clock"].split(":"))
        if (not a or not b or a == b or hours > 23 or minutes > 59
                or s1 > 20 or s2 > 20 or h1 > s1 or h2 > s2):
            invalid.append("invalid_score_or_team")
            continue
        matches.append((a, b, s1, s2))
    meta = DECLARED.search(text)
    declared = int(meta.group(1)) if meta else None
    team_meta = DECLARED_TEAMS.search(text)
    declared_teams = int(team_meta.group(1)) if team_meta else None
    home = Counter(x[0] for x in matches)
    away = Counter(x[1] for x in matches)
    teams = set(home) | set(away)
    directed_pairs = set((x[0], x[1]) for x in matches)
    balanced = (len(teams) == expected_teams and all(
        home[t] == expected_teams - 1 and away[t] == expected_teams - 1
        for t in teams))
    complete = (len(matches) == expected_matches and
                declared == expected_matches and
                declared_teams == expected_teams and
                len(directed_pairs) == expected_matches and
                balanced and not invalid)
    return {
        "declared_matches": declared,
        "declared_teams": declared_teams,
        "parsed_scores": len(matches),
        "teams": len(teams),
        "unique_home_away_pairs": len(directed_pairs),
        "balanced_home_away": balanced,
        "invalid_lines_count": len(invalid),
        "structurally_complete": complete,
        "independently_result_verified": False,
        "fixture_dates_verified": False,
        "approved_for_forecasts": False,
    }


def run(output=OUTPUT, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timestamp must have time zone")
    doc = {
        "kind": "readonly_independent_source_structural_audit",
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "season": "2025/26",
        "license_declared_by_repositories": "CC0-1.0; upstream contribution rights still need review",
        "automatic_promotion": False,
        "models_modified": False,
        "leagues": {},
    }
    lines = [
        "# RZOTKIEWKA — niezależne archiwa 2025/26 (badanie, nie prognozy)",
        "",
        "Źródła: OpenFootball, commit-pinned, deklaracja licencji CC0.",
        "Kontrola UTC: " + doc["observed_at_utc"],
        "**Zgodna struktura nie dowodzi poprawności poszczególnych wyników ani dat.**",
        "**Brak automatycznego dopuszczenia ligi, aktualizacji modelu lub LIVE.**",
        "",
        "| Liga | Deklarowane | Rozpoznane wyniki | Drużyny | 19+19 | Struktura |",
        "|---|---:|---:|---:|---|---|",
    ]
    for league, spec in SOURCES.items():
        item = {
            "source_url": source_url(spec),
            "source_repo": "https://github.com/" + spec["repo"],
            "source_commit": spec["commit"],
            "source_license": ("https://github.com/" + spec["repo"] + "/blob/" +
                               spec["commit"] + "/LICENSE.md"),
            "approved_for_forecasts": False,
        }
        try:
            raw = fetch_text(spec)
            item.update(assess_text(raw))
            item["sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            item["read_ok"] = True
        except (HTTPError, URLError, TimeoutError, ValueError, OSError,
                UnicodeError) as exc:
            item["read_ok"] = False
            item["error"] = type(exc).__name__ + ": " + str(exc)[:160]
        doc["leagues"][league] = item
        if item["read_ok"]:
            lines.append("| " + league + " | " + str(item["declared_matches"]) +
                         " | " + str(item["parsed_scores"]) + " | " +
                         str(item["teams"]) + " | " +
                         ("TAK" if item["balanced_home_away"] else "NIE") + " | " +
                         ("OK" if item["structurally_complete"] else "NIEKOMPLETNA") + " |")
        else:
            lines.append("| " + league + " | — | — | — | — | NIEPOTWIERDZONA |")
            lines.append("Błąd odczytu: " + item["error"])
        lines.append("Dane: " + item["source_url"])
    lines += [
        "", "## Co jeszcze musimy potwierdzić",
        "- Wyniki i terminy na próbie porównać z niezależnym wiarygodnym źródłem.",
        "- Porównać nazwy drużyn i poprawnie przypisać sezony (bez zgadywania).",
        "- Sprawdzić zakres CC0 dla wkładów osób trzecich przed komercyjnym wdrożeniem.",
        "- Stworzyć osobny adapter i backtest bez wpływu na LAB 2.1/2.2.",
        "- Nie modyfikować produkcyjnych prognoz ani danych i nie kupować usług.",
        "",
    ]
    output.mkdir(parents=True, exist_ok=True)
    body = "\n".join(lines)
    (output / "OPENFOOTBALL_HISTORIA_2025.md").write_text(body, encoding="utf-8")
    (output / "openfootball_historia_2025.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    print(body)
    if __import__("os").environ.get("GITHUB_STEP_SUMMARY"):
        with open(__import__("os").environ["GITHUB_STEP_SUMMARY"], "a",
                  encoding="utf-8") as f:
            f.write(body)
    return doc


if __name__ == "__main__":
    run()

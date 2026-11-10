#!/usr/bin/env python3
"""Second-stage UCL fixture-data audit. Read-only, no predictions or promotion.

Audits three OpenLigaDB seasons (previous two plus current), highlighting
coverage and suspicious scheduling/score records. Positive is manual review
ONLY and is not evidence of forecast quality or licensing approval.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from league_candidates import get_matches, normalize, accepted_final_score

OUTPUT = Path("league_audit")
MIN_PREVIOUS_FINISHED = 80
MIN_CURRENT_FINISHED = 10
MIN_CURRENT_FUTURE = 1


def inspect_season(payload, year, now):
    if not isinstance(payload, list):
        raise ValueError("Expected a list of UCL fixtures")
    valid = []
    malformed = 0
    group_missing = 0
    suspicious_goals = 0
    for raw in payload:
        rec = normalize(raw)
        if rec is None:
            malformed += 1
            continue
        raw_group = raw.get("group")
        if not isinstance(raw_group, dict) or not str(raw_group.get("groupName") or "").strip():
            group_missing += 1
        score = accepted_final_score(raw)
        if score is not None and max(score) >= 12:
            suspicious_goals += 1
        valid.append((rec, raw["team1"]["teamId"], raw["team2"]["teamId"]))
    ids = [rec["id"] for rec, _, _ in valid]
    duplicate_ids = len(ids) - len(set(ids))
    # Leg 1 / leg 2 are allowed on different days. Only identical pair/date is suspicious.
    pair_days = [(rec["kickoff"].date().isoformat(), min(home, away), max(home, away))
                 for rec, home, away in valid]
    duplicate_pair_days = sum(v - 1 for v in Counter(pair_days).values() if v > 1)
    ended = [rec for rec, _, _ in valid if rec["score"] is not None and rec["kickoff"] <= now]
    overdue = [rec for rec, _, _ in valid
               if rec["score"] is None and rec["kickoff"] <= now - timedelta(hours=48)]
    in_future = [rec for rec, _, _ in valid
                 if rec["kickoff"] > now and not rec["finished_flag"]]
    future_results = sum(rec["kickoff"] > now and
                         (rec["score"] is not None or rec["finished_flag"])
                         for rec, _, _ in valid)
    bad_finish_flags = sum(rec["finished_flag"] and rec["score"] is None
                           for rec, _, _ in valid)
    start = datetime(year, 7, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 7, 1, tzinfo=timezone.utc)
    out_of_season = sum(not start <= rec["kickoff"] < end for rec, _, _ in valid)
    all_teams = {tid for _, home, away in valid for tid in (home, away)}
    return {
        "season": year,
        "raw_matches": len(payload),
        "valid_matches": len(valid),
        "malformed_matches": malformed,
        "unique_teams": len(all_teams),
        "finished_with_score": len(ended),
        "future_scheduled": len(in_future),
        "overdue_48h_missing_score": len(overdue),
        "finished_flag_without_score": bad_finish_flags,
        "future_but_marked_finished": future_results,
        "duplicate_match_ids": duplicate_ids,
        "duplicate_pair_same_day": duplicate_pair_days,
        "matches_outside_july_june_season": out_of_season,
        "missing_group_name": group_missing,
        "extreme_scores_12plus": suspicious_goals,
        "first_kickoff_utc": min((rec["kickoff"].isoformat() for rec, _, _ in valid), default=None),
        "last_kickoff_utc": max((rec["kickoff"].isoformat() for rec, _, _ in valid), default=None),
        "all_match_ids": ids,
    }


def decide(blocks):
    issues = []
    for block in blocks:
        year = block["season"]
        if block.get("error"):
            issues.append(f"{year}: API / odczyt niedostępny")
            continue
        for field, label in (
            ("malformed_matches", "niepoprawne rekordy"),
            ("duplicate_match_ids", "powtórzone ID"),
            ("duplicate_pair_same_day", "podwójne pary tego samego dnia"),
            ("overdue_48h_missing_score", "zaległe spotkania bez wyniku"),
            ("finished_flag_without_score", "mecze zakończone bez wyniku"),
            ("future_but_marked_finished", "przyszłe mecze oznaczone jako zakończone"),
            ("matches_outside_july_june_season", "daty poza sezonem lipiec–czerwiec"),
        ):
            if block[field]:
                issues.append(f"{year}: {label} ({block[field]})")
    if all("error" not in b for b in blocks):
        seen = {}
        for block in blocks:
            for ident in block["all_match_ids"]:
                if ident in seen and seen[ident] != block["season"]:
                    issues.append(f"ID meczu {ident} występuje w sezonach {seen[ident]} i {block['season']}")
                seen[ident] = block["season"]
        for block in blocks[:-1]:
            if block["finished_with_score"] < MIN_PREVIOUS_FINISHED:
                issues.append(f"{block['season']}: za mało rozliczonych meczów ({block['finished_with_score']})")
        current = blocks[-1]
        if current["finished_with_score"] < MIN_CURRENT_FINISHED:
            issues.append(f"{current['season']}: za mało aktualnych wyników")
        if current["future_scheduled"] < MIN_CURRENT_FUTURE:
            issues.append(f"{current['season']}: brak przyszłych meczów")
    # No auto-accept; a clean result is only an invitation to manual audit.
    return ("DO RĘCZNEGO SPRAWDZENIA" if not issues else
            "WYMAGA WYJAŚNIENIA", list(dict.fromkeys(issues)))


def run(now=None, output=OUTPUT):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Audit time requires timezone")
    season = now.year if now.month >= 7 else now.year - 1
    blocks = []
    for year in (season - 2, season - 1, season):
        try:
            data = get_matches("ucl", year)
            block = inspect_season(data, year, now)
        except (Exception) as exc:
            # The report must explicitly state unavailable API instead of claiming a pass.
            block = {"season": year, "error": type(exc).__name__ + ": " + str(exc)[:160]}
        blocks.append(block)
    status, issues = decide(blocks)
    public_blocks = [{k: v for k, v in block.items() if k != "all_match_ids"} for block in blocks]
    report = {
        "type": "RZOTKIEWKA_UCL_SECOND_STAGE_READ_ONLY",
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "source": "https://api.openligadb.de/getmatchdata/ucl/{year}",
        "status": status, "issues": issues,
        "models_changed": False, "automatic_admission": False,
        "seasons": public_blocks,
    }
    lines = [
        "# RZOTKIEWKA — Liga Mistrzów: pogłębiony audyt",
        "",
        "Stan UTC: " + report["observed_at_utc"],
        "",
        "**" + status + "** — to NIE oznacza dopuszczenia do prognoz 1X2.",
        "Dane z OpenLigaDB; brak niezależnej weryfikacji meczów z UEFA.",
        "",
        "| Sezon | Rekordy | Wyniki | Nadchodzące | Zaległe >48 h | Duplikaty ID |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for block in public_blocks:
        val = lambda k: str(block.get(k, "—"))
        lines.append("| " + str(block["season"]) + "/" + str(block["season"]+1) +
                     " | " + val("raw_matches") + " | " + val("finished_with_score") +
                     " | " + val("future_scheduled") + " | " +
                     val("overdue_48h_missing_score") + " | " +
                     val("duplicate_match_ids") + " |")
    lines.extend(["", "## Wykryte kwestie"])
    lines.extend(["- " + item for item in issues] if issues else
                 ["- Nie wykryto niezgodności objętych tą kontrolą."])
    lines.extend([
        "", "## Dodatkowe ograniczenia",
        "- Bez niezależnego porównania terminów i rezultatów z UEFA nie potwierdzamy zgodności.",
        "- Liczba meczów, dostępność sezonu i licencja danych wymagają ręcznej oceny.",
        "- Brak danych nie jest zastępowany symulacją ani sztuczną prognozą.",
        "- Nie dokonano żadnych zmian w archiwum, LAB 2.1/2.2 ani silniku 1X2.",
        "",
    ])
    output.mkdir(parents=True, exist_ok=True)
    (output / "UCL_AUDYT.md").write_text("\n".join(lines), encoding="utf-8")
    (output / "UCL_AUDYT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
    return report


if __name__ == "__main__":
    run()

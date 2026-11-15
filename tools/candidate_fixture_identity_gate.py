#!/usr/bin/env python3
"""Read-only identity check for candidate Premier League / LaLiga fixture feeds.

This is NOT a release gate approval. Source labels and team IDs from one feed
cannot independently establish competition identity. No network, commits,
predictions, publishing, or automatic promotion happen here.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# The audited, dated official 2026/27 name rosters already used for research.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api_football_official_roster import OFFICIAL  # noqa: E402
from api_football_crosscheck import clean_team  # noqa: E402

SEASON = 2026
MAX_FIXTURES = 600
ZONED_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$")
ALLOWED = frozenset({39, 140})


def evaluate_fixtures(records, league_id, season=SEASON):
    """Return conservative research findings; NEVER approve production release."""
    report = {
        "kind": "candidate_fixture_identity_research",
        "league_id": league_id,
        "season": season,
        "candidate_count": len(records) if isinstance(records, list) else None,
        "official_roster_source": None,
        "status": "BLOCKED",
        "blocking_reasons": [],
        "production_release_allowed": False,
        "public_fixture_preview_allowed": False,
        "predictions_allowed": False,
    }
    issues = report["blocking_reasons"]
    if type(league_id) is not int or league_id not in ALLOWED or type(season) is not int or season != SEASON:
        issues.append("No supported, season-specific official roster for this competition.")
        return report

    reference = OFFICIAL[league_id]
    if reference.get("season") != "2026/27" or not reference.get("url"):
        issues.append("Official roster provenance or season is missing.")
        return report
    report["official_roster_source"] = reference["url"]
    expected = {clean_team(name) for name in reference["clubs"]}
    if len(expected) != 20:
        issues.append("Official club-name roster is not a unique 20-club set.")
        return report
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_FIXTURES:
        issues.append("Fixture payload must be a nonempty, bounded list.")
        return report

    seen_matches, id_to_name, name_to_id = set(), {}, {}
    for position, row in enumerate(records):
        prefix = "fixture " + str(position + 1)
        if not isinstance(row, dict):
            issues.append(prefix + ": malformed record")
            continue
        match_id = row.get("matchID")
        if type(match_id) is not int or match_id <= 0 or match_id in seen_matches:
            issues.append(prefix + ": missing or duplicate match ID")
        else:
            seen_matches.add(match_id)

        raw_time = row.get("matchDateTimeUTC")
        if not isinstance(raw_time, str) or not ZONED_UTC.fullmatch(raw_time):
            issues.append(prefix + ": UTC kickoff with explicit timezone required")
        else:
            try:
                from datetime import datetime
                datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            except ValueError:
                issues.append(prefix + ": invalid calendar date")

        home_id = away_id = None
        for side in ("team1", "team2"):
            team = row.get(side)
            if not isinstance(team, dict):
                issues.append(prefix + ": " + side + " missing")
                continue
            name, team_id = team.get("teamName"), team.get("teamId")
            if not isinstance(name, str) or not name.strip() or type(team_id) is not int or team_id <= 0:
                issues.append(prefix + ": " + side + " lacks valid name/ID")
                continue
            normalized = clean_team(name)
            if normalized not in expected:
                # Never guess aliases from a similarly spelled or foreign club.
                issues.append(prefix + ": " + side + " is outside verified name roster: " + name[:65])
            if team_id in id_to_name and id_to_name[team_id] != normalized:
                issues.append(prefix + ": one team ID maps to different names")
            if normalized in name_to_id and name_to_id[normalized] != team_id:
                issues.append(prefix + ": one club name maps to different IDs")
            id_to_name[team_id] = normalized
            name_to_id[normalized] = team_id
            if side == "team1":
                home_id = team_id
            else:
                away_id = team_id
        if home_id is not None and home_id == away_id:
            issues.append(prefix + ": same club on both sides")

    # Suppress repetitive evidence; retain a bounded diagnostic summary.
    report["blocking_reasons"] = list(dict.fromkeys(issues))[:30]
    if not issues:
        report["status"] = "NAMES_CONSISTENT_NEEDS_INDEPENDENT_REVIEW"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only competition fixture identity audit.")
    parser.add_argument("--input", type=Path, required=True, help="Existing local JSON list, never fetched")
    parser.add_argument("--league-id", type=int, required=True, choices=(39, 140))
    parser.add_argument("--season", type=int, default=SEASON)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        result = evaluate_fixtures(data, args.league_id, args.season)
    except (OSError, ValueError, UnicodeError) as exc:
        print("Fixture audit could not read valid local JSON: " + type(exc).__name__, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "NAMES_CONSISTENT_NEEDS_INDEPENDENT_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())

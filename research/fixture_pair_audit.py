"""Offline-only match identity comparison across already acquired sources.

No API calls, writes, publishing, or fuzzy team-name matching.
The required team-ID crosswalk must be approved separately.
Matching historical scores does not validate a forward forecast or licensing.
"""
from collections import Counter
from datetime import datetime, timezone


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("kickoff_utc must be a timezone-aware ISO 8601 string")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid kickoff_utc") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("missing kickoff timezone")
    return dt.astimezone(timezone.utc)


def _positive_id(value):
    return type(value) is int and value > 0


def _score(row):
    h, a = row.get("home_goals"), row.get("away_goals")
    if any(type(x) is not int or x < 0 for x in (h, a)):
        raise ValueError("missing or invalid final score")
    return h, a


def audit_pairs(api_rows, independent_rows, approved_team_ids, *, max_hours=24):
    """Return aggregate counters; fail closed on malformed input.

    API rows: fixture_id, league_id, season, kickoff_utc,
              home_team_id, away_team_id, home_goals, away_goals.
    Independent rows: league_id, season, kickoff_utc,
                      home_team_code, away_team_code, home_goals, away_goals.
    Approval map: API numeric team ID -> independent canonical team code.
    No aliases are inferred or accepted automatically.
    """
    if not 0 <= max_hours <= 48:
        raise ValueError("invalid comparison window")
    if not isinstance(api_rows, list) or not isinstance(independent_rows, list):
        raise ValueError("input records must be lists")
    if not isinstance(approved_team_ids, dict):
        raise ValueError("explicit approval map required")
    if any(not _positive_id(k) or not isinstance(v, str) or not v.strip()
           for k, v in approved_team_ids.items()):
        raise ValueError("invalid approval map")
    if len(set(approved_team_ids.values())) != len(approved_team_ids):
        raise ValueError("two API team ids map to same canonical team")

    seen_api = set()
    seen_match_identity = set()
    validated_api = []
    for row in api_rows:
        if not isinstance(row, dict):
            raise ValueError("malformed API record")
        fid, league, season = (row.get(k) for k in ("fixture_id", "league_id", "season"))
        home, away = row.get("home_team_id"), row.get("away_team_id")
        if any(not _positive_id(x) for x in (fid, league, home, away)) or home == away:
            raise ValueError("invalid API identifiers")
        if type(season) is not int or not 2010 <= season <= 2100:
            raise ValueError("invalid season")
        identity = (league, season, fid)
        if identity in seen_api:
            raise ValueError("duplicate API fixture identifier")
        seen_api.add(identity)
        kickoff = _utc(row.get("kickoff_utc"))
        match_identity = (league, season, home, away, kickoff)
        if match_identity in seen_match_identity:
            raise ValueError("same scheduled match has multiple fixture ids")
        seen_match_identity.add(match_identity)
        validated_api.append((league, season, kickoff, home, away, _score(row)))

    indexed = {}
    for reference_index, row in enumerate(independent_rows):
        if not isinstance(row, dict):
            raise ValueError("malformed independent record")
        league, season = row.get("league_id"), row.get("season")
        home, away = row.get("home_team_code"), row.get("away_team_code")
        if not _positive_id(league) or type(season) is not int or not 2010 <= season <= 2100:
            raise ValueError("invalid reference league/season")
        if not isinstance(home, str) or not isinstance(away, str) or not home.strip() or not away.strip() or home == away:
            raise ValueError("invalid reference teams")
        key = (league, season, home, away)
        indexed.setdefault(key, []).append((reference_index, _utc(row.get("kickoff_utc")), _score(row)))

    counts = Counter(api_records=len(validated_api), reference_records=len(independent_rows),
                     agreed=0, different_score=0, different_date=0, not_found=0,
                     ambiguous=0, unmapped_team=0)
    used_reference_records = set()
    for league, season, kickoff, home, away, goals in validated_api:
        if home not in approved_team_ids or away not in approved_team_ids:
            counts["unmapped_team"] += 1
            continue
        candidates = indexed.get((league, season, approved_team_ids[home], approved_team_ids[away]), [])
        if not candidates:
            counts["not_found"] += 1
            continue
        near = [(reference_index, date, score) for reference_index, date, score in candidates
                if abs((date - kickoff).total_seconds()) <= max_hours * 3600]
        if not near:
            counts["different_date"] += 1
        elif len(near) > 1:
            counts["ambiguous"] += 1
        else:
            reference_index, reference_date, reference_score = near[0]
            if reference_index in used_reference_records:
                raise ValueError("one independent match was reused for multiple fixtures")
            # The matching window is only for locating possible candidates.
            # A differing kickoff, even with identical score, cannot establish agreement.
            if reference_date != kickoff:
                counts["different_date"] += 1
                continue
            used_reference_records.add(reference_index)
            if reference_score != goals:
                counts["different_score"] += 1
            else:
                counts["agreed"] += 1
    return dict(counts)

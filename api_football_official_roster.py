"""Research-only: compare OpenFootball and API names with official 2026/27 league rosters.

Official club spellings: checked manually against season-specific league pages
on 2026-11-11. This is an *independent names roster*, not proof that an
API provider team ID is the same entity, or a rights/license certification.

Only aggregated numbers are output. No API names, IDs or fixtures are stored.
"""
from collections import Counter
import os
import sys
from datetime import date

from api_football_alias_candidates import GENERIC, propose_names, tokens
from api_football_crosscheck import SOURCES, SEASON, clean_team, read_openfootball_matches
from api_football_league_catalog import check_quota
from api_football_probe import api_get, verify_subscription
from api_football_team_id_audit import read_roster
from openfootball_history_audit import fetch_text

OFFICIAL = {
    39: {
        "url": "https://www.premierleague.com/en/news/4365156/premier-leagues-beginners-guide-all-you-need-to-know",
        "season": "2026/27",
        "observed": "2026-11-11",
        "clubs": (
            "AFC Bournemouth", "Arsenal", "Aston Villa", "Brentford",
            "Brighton & Hove Albion", "Chelsea", "Coventry City",
            "Crystal Palace", "Everton", "Fulham", "Hull City",
            "Ipswich Town", "Leeds United", "Liverpool", "Manchester City",
            "Manchester United", "Newcastle United", "Nottingham Forest",
            "Sunderland", "Tottenham Hotspur",
        ),
    },
    140: {
        "url": "https://www.laliga.com/en-US/laliga-easports/clubs",
        "season": "2026/27",
        "observed": "2026-11-11",
        "clubs": (
            "Athletic Club", "Atlético de Madrid", "CA Osasuna", "Celta",
            "Deportivo Alavés", "Elche CF", "FC Barcelona", "Getafe CF",
            "Levante UD", "Málaga CF", "R. Racing Club", "Rayo Vallecano",
            "RC Deportivo", "RCD Espanyol de Barcelona", "Real Betis",
            "Real Madrid", "Real Sociedad", "Sevilla FC", "Valencia CF",
            "Villarreal CF",
        ),
    },
}

# A short league label is linked to explicitly documented FULL names of the
# SAME club, as published by the league and the club itself on 2026-11-11.
# Source: https://www.laliga.com/es-GB/clubes/rc-deportivo
# Source: https://www.rcdeportivo.es/es/datos-generales
# Club explanation: https://www.rcdeportivo.es/es/noticias/preguntas-y-respuestas-referentes-a-la-consulta-vinculante-sobre-la-denominacion-oficial-del-clu
# This is research-only lexical evidence, never an approved API team mapping.
OFFICIAL_FULL_NAME_EVIDENCE = {
    140: {
        "rc deportivo": (
            "Real Club Deportivo de A Coruña",
            "Real Club Deportivo de La Coruña",
        ),
    },
}
TRAIN_START = date(2026, 8, 21)
TRAIN_END = date(2026, 8, 31)


def validate_registry(official):
    if not isinstance(official, (tuple, list)) or len(official) != 20:
        raise ValueError("Oficjalna lista sezonu musi miec 20 klubow.")
    normalized = [clean_team(name) for name in official]
    if any(not n for n in normalized) or len(set(normalized)) != len(normalized):
        raise ValueError("Oficjalna lista zawiera powtorzenia lub puste nazwy.")
    return normalized


def official_pivot(name, official, full_names=None):
    """Return one official normalized club name, or None / 'ambiguous'.

    Exact names take priority. Loose lexical proposals require a unique
    distinctive token across the official roster, plus token subset.
    Never infer identity from match scores, team ID or edit distance.
    """
    canonical = validate_registry(official)
    n = clean_team(name)
    if not n:
        return None
    if n in canonical:
        return n
    t = tokens(n)
    if not t:
        return None
    full_names = full_names or {}
    if any(short not in canonical for short in full_names):
        raise ValueError("Dowod pelnej nazwy nie wskazuje klubu z listy.")
    # Count any distinctive token ONCE PER OFFICIAL CLUB, not once per form.
    official_forms = {
        name: [tokens(name)] + [tokens(full) for full in full_names.get(name, ())]
        for name in canonical
    }
    freq = Counter(
        tok for forms in official_forms.values()
        for tok in set().union(*forms)
    )
    opts = []
    for official_name, forms in official_forms.items():
        for parts in forms:
            distinctive = {
                tok for tok in t & parts
                if len(tok) >= 5 and tok not in GENERIC and freq[tok] == 1
            }
            if distinctive and (parts <= t or t <= parts):
                opts.append(official_name)
                break
    if len(opts) == 1:
        return opts[0]
    if len(opts) > 1:
        return "ambiguous"
    return None


def join_teams_to_official(names, official, full_names=None):
    mapping = {
        name: official_pivot(name, official, full_names) for name in names
    }
    pivot_counts = Counter(x for x in mapping.values() if x not in (None, "ambiguous"))
    return mapping, {
        "recognized": sum(x not in (None, "ambiguous") for x in mapping.values()),
        "unresolved": sum(x is None for x in mapping.values()),
        "ambiguous": sum(x == "ambiguous" for x in mapping.values()),
        "official_collisions": sum(n - 1 for n in pivot_counts.values() if n > 1),
    }


def triangulate(source_names, provider_names, league_id):
    reference = OFFICIAL[league_id]
    official = reference["clubs"]
    validate_registry(official)
    sources = set(source_names)
    api = set(provider_names)
    full_names = OFFICIAL_FULL_NAME_EVIDENCE.get(league_id, {})
    src_pivot, src_stats = join_teams_to_official(sources, official, full_names)
    api_pivot, api_stats = join_teams_to_official(api, official, full_names)
    proposals, _counts = propose_names(sources, api)
    supported = unresolved = conflicting = 0
    for src, api_name in proposals.items():
        s = src_pivot[src]
        a = api_pivot[api_name]
        if s in (None, "ambiguous") or a in (None, "ambiguous"):
            unresolved += 1
        elif s == a:
            supported += 1
        else:
            conflicting += 1
    if supported + unresolved + conflicting != len(proposals):
        raise RuntimeError("Bledne zliczenie kandydatow.")
    collisions = src_stats["official_collisions"] + api_stats["official_collisions"]
    # Even identical mapped names are evidence to REVIEW, never approved.
    return {
        "official_roster_clubs": len(official),
        "openfootball_clubs": len(sources),
        "api_clubs": len(api),
        "proposed_aliases": len(proposals),
        "official_name_support": supported,
        "unresolved_official_name": unresolved,
        "conflicting_official_name": conflicting,
        "official_roster_source_matches": src_stats["recognized"],
        "official_roster_api_matches": api_stats["recognized"],
        "official_roster_name_ambiguities": src_stats["ambiguous"] + api_stats["ambiguous"],
        "official_roster_name_collisions": collisions,
        "auto_approved_aliases": 0,
        "ready_for_manual_review": supported if not collisions else 0,
    }


def run(key):
    status = verify_subscription(api_get("status", key))
    check_quota(status, needed=len(SOURCES), reserve=100)
    print("RZOTKIEWKA: porownanie nazw klubow z oficjalnymi listami lig 2026/27.")
    print("Oficjalne wykazy odczytane i przepisane do jawnego rejestru 11.11.2026; "
          "nie sa odswiezane automatycznie. To tylko porownanie nazw.")
    print(f"Zaplacony plan PRO, zapytania wykorzystane przed audytem: {status['used_today']}; "
          "maksymalnie 2 wywolania /teams.")
    for league, label, source_spec in SOURCES:
        historical = read_openfootball_matches(
            fetch_text(source_spec), TRAIN_START, TRAIN_END)
        source_names = {name for _, home, away, _ in historical for name in (home, away)}
        roster, _ = read_roster(api_get("teams", key, {
            "league": str(league), "season": str(SEASON),
        }))
        stats = triangulate(source_names, roster.values(), league)
        print(label + ": " + " ".join(f"{key}={value}" for key,value in stats.items()))
    print("Potwierdzenie nazw nie jest dowodem poprawnego mapowania konkretnego team ID "
          "ani zgody na komercyjne rozpowszechnianie danych. "
          "Zadne aliasy ani modele nie zostaly dopuszczone do produkcji.")


if __name__ == "__main__":
    try:
        run(os.environ.get("API_FOOTBALL_KEY", ""))
    except (OSError, RuntimeError, UnicodeError, ValueError) as err:
        sys.exit(f"Badanie list oficjalnych nieudane: {type(err).__name__}.")

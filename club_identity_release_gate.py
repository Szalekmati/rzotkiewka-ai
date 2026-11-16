"""Fail-closed release gate for additional leagues and API-FOOTBALL club aliases.

Audit success and officially supported team NAMES are not verified team IDs,
commercial redistribution permission, or forward-time prediction validation.
This script never retrieves API data or modifies production files.
"""
import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlparse

from api_football_official_roster import OFFICIAL

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "data" / "identity_release_registry.json"
BLOCKED_PROOF_HOSTS = ("api-football.com", "api-sports.io", "github.com", "githubusercontent.com")


def _required(entry, keys):
    if not isinstance(entry, dict) or any(k not in entry for k in keys):
        raise ValueError("Brak wymaganych pol rejestru.")
    return entry


def _date(value):
    if not isinstance(value, str):
        raise ValueError("Brak daty przegladu.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("Nieprawidlowa data przegladu.") from None


def _https(value, independent=False):
    if not isinstance(value, str):
        raise ValueError("Brak URL dowodu.")
    parts = urlparse(value)
    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
        raise ValueError("Dowod wymaga publicznego HTTPS.")
    host = (parts.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"} or "." not in host:
        raise ValueError("Nieprawidlowy host dowodu.")
    if independent and any(host == domain or host.endswith("." + domain)
                           for domain in BLOCKED_PROOF_HOSTS):
        raise ValueError("Dowod tozsamosci musi byc niezalezny od dostawcy/API i repozytorium.")
    return value


def _club_identity_proof_url(value, official_roster_url):
    """Reject generic directory URLs; this never verifies a team ID by itself."""
    _https(value, independent=True)
    submitted = urlparse(value)
    official = urlparse(official_roster_url)
    path = submitted.path.rstrip("/").casefold()
    official_path = official.path.rstrip("/").casefold()
    generic_paths = {"/", "", "/clubs", "/en/clubs", "/en-us/laliga-easports/clubs",
                     "/en/laliga-easports/clubs"}
    if (path in generic_paths or
            (submitted.hostname or "").casefold() == (official.hostname or "").casefold()
            and path == official_path):
        raise ValueError("Wymagany indywidualny dowod dotyczacy konkretnego klubu.")
    # A plausible link is not independent verification of a provider team ID.
    return value


def _count(value, maximum=None):
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError("Nieprawidlowa liczba zweryfikowanych klubow.")
    return value


def inspect(registry):
    _required(registry, ("schema_version", "project", "review_date",
                         "competitions", "reviewed_identity_links", "release"))
    if registry["schema_version"] != 1 or registry["project"] != "RZOTKIEWKA AI":
        raise ValueError("Nieznana wersja schematu lub projekt.")
    _date(registry["review_date"])
    competitions = registry["competitions"]
    if not isinstance(competitions, list) or not competitions:
        raise ValueError("Brak lig w rejestrze.")
    ids = set()
    groups = {}
    for group in competitions:
        _required(group, ("league_id", "league", "season", "candidate_aliases",
                          "name_supported_by_official_roster",
                          "mapped_inside_api_to_unique_id",
                          "independently_reviewed_club_ids",
                          "official_roster_url", "audit_url"))
        league_id, season = group["league_id"], group["season"]
        if (type(league_id) is not int or league_id <= 0 or
                type(season) is not int or not 2000 <= season <= 2100 or
                not isinstance(group["league"], str) or not group["league"].strip()):
            raise ValueError("Nieprawidlowa liga, nazwa lub sezon.")
        key = (league_id, season)
        if key in ids:
            raise ValueError("Zduplikowana liga i sezon.")
        ids.add(key)
        candidate_count = _count(group["candidate_aliases"])
        name_count = _count(group["name_supported_by_official_roster"], candidate_count)
        internally_linked = _count(group["mapped_inside_api_to_unique_id"], candidate_count)
        _count(group["independently_reviewed_club_ids"], min(name_count, internally_linked))
        _https(group["official_roster_url"])
        _https(group["audit_url"])
        official = OFFICIAL.get(league_id)
        expected_season = f"{season}/{(season + 1) % 100:02d}"
        if (not official or official["season"] != expected_season or
                group["official_roster_url"] != official["url"]):
            raise ValueError("Brak odpowiedniego oficjalnego wykazu ligi/sezonu.")
        groups[key] = group

    records = registry["reviewed_identity_links"]
    if not isinstance(records, list):
        raise ValueError("Lista powiazan musi byc lista.")
    by_competition = Counter()
    seen_source = set()
    seen_provider_id = set()
    seen_official_club = set()
    for link in records:
        _required(link, ("league_id", "season", "source_team_name",
                         "official_club_name", "provider_team_id",
                         "independent_identity_url", "reviewed_by", "reviewed_on"))
        key = (link["league_id"], link["season"])
        if key not in groups:
            raise ValueError("Powiazanie bez zarejestrowanej ligi.")
        if (type(link["provider_team_id"]) is not int or link["provider_team_id"] <= 0
                or any(not isinstance(link[field], str) or not link[field].strip()
                       for field in ("source_team_name", "official_club_name", "reviewed_by"))):
            raise ValueError("Brak jednoznacznej nazwy, ID lub osoby weryfikujacej.")
        if _date(link["reviewed_on"]) > _date(registry["review_date"]):
            raise ValueError("Dowod jest z przyszlosci wobec rejestru.")
        _club_identity_proof_url(link["independent_identity_url"], groups[key]["official_roster_url"])
        official_name = link["official_club_name"].strip()
        if official_name not in OFFICIAL[key[0]]["clubs"]:
            raise ValueError("Klub spoza oficjalnego wykazu ligi i sezonu.")
        source = (key, link["source_team_name"].strip().casefold())
        provider = (key, link["provider_team_id"])
        official_club = (key, official_name)
        if (source in seen_source or provider in seen_provider_id or
                official_club in seen_official_club):
            raise ValueError("Powtorzony klub, oficjalna nazwa albo ID w lidze.")
        seen_source.add(source)
        seen_provider_id.add(provider)
        seen_official_club.add(official_club)
        by_competition[key] += 1
    for key, group in groups.items():
        if by_competition[key] != group["independently_reviewed_club_ids"]:
            raise ValueError("Liczba przegladnietych ID nie zgadza sie z dowodami.")

    release = _required(registry["release"], (
        "requested", "rights_review_approved", "rights_review_document_url",
        "forward_time_model_test_approved", "forward_time_test_report_url",
        "authorized_by", "authorized_on", "decision_url"))
    for field in ("requested", "rights_review_approved", "forward_time_model_test_approved"):
        if type(release[field]) is not bool:
            raise ValueError("Flagi zgody musza byc wartosciami logicznymi.")
    if release["rights_review_approved"]:
        _https(release["rights_review_document_url"])
    if release["forward_time_model_test_approved"]:
        _https(release["forward_time_test_report_url"])

    reasons = []
    expected_identity_links = sum(g["candidate_aliases"] for g in competitions)
    if not records:
        reasons.append("brak indywidualnych, niezaleznie zweryfikowanych ID")
    if len(records) != expected_identity_links:
        reasons.append(
            f"niepelna kontrola ID: {len(records)}/{expected_identity_links} kandydatow"
        )
    if not release["rights_review_approved"]:
        reasons.append("brak formalnej kontroli praw do wykorzystania danych")
    if not release["forward_time_model_test_approved"]:
        reasons.append("brak zaakceptowanego testu prognoz przedmeczowych")
    if not release["requested"]:
        reasons.append("brak jawnego wniosku o wdrozenie")
    if release["requested"]:
        if (not isinstance(release["authorized_by"], str) or
                not release["authorized_by"].strip() or not release["authorized_on"]):
            reasons.append("brak podpisanej decyzji o wdrozeniu")
        else:
            _date(release["authorized_on"])
        if not release["decision_url"]:
            reasons.append("brak linku do zatwierdzonej decyzji")
        else:
            _https(release["decision_url"])
    if release["requested"] and reasons:
        raise ValueError("Blokada wdrozenia: " + "; ".join(reasons))
    return {
        "checked_competitions": len(competitions),
        "name_supported_alias_candidates": sum(g["name_supported_by_official_roster"] for g in competitions),
        "independently_verified_id_links": len(records),
        "production_release_allowed": False,  # REQUIRES A SEPARATE, REVIEWED RELEASE IMPLEMENTATION.
        "blocked_reasons": reasons,
    }


def main():
    p = argparse.ArgumentParser(description="Offline: sprawdz bramke tozsamosci dla nowych lig")
    p.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    p.add_argument("--require-release", action="store_true",
                   help="Odrzuc dopoki odrebne wdrozenie nie zostanie zatwierdzone")
    args = p.parse_args()
    try:
        data = json.loads(args.registry.read_text(encoding="utf-8"))
        result = inspect(data)
        print("RZOTKIEWKA - kontrola rejestru tozsamosci: SCHEMAT_OK")
        print(f"Ligi: {result['checked_competitions']}; "
              f"oficjalnie wspierane kandydatury nazw: {result['name_supported_alias_candidates']}; "
              f"niezaleznie zweryfikowane mapy ID: {result['independently_verified_id_links']}.")
        print("PRODUKCJA NOWYCH LIG: ZABLOKOWANA. "
              "Zielone testy kodu NIE oznaczaja zatwierdzenia danych.")
        for reason in result["blocked_reasons"]:
            print("Do zrobienia: " + reason)
        if args.require_release:
            p.exit(2, "Nowe ligi nie sa zatwierdzone do wdrozenia.\n")
    except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
        p.exit(1, "Blad walidacji rejestru tozsamosci: " + type(exc).__name__ + ".\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""RZOTKIEWKA AI 2.3: niezależny audyt offline prognoz 1X2.

Tylko odczyt danych; NIE zmienia silnika prognoz ani strony WWW.
Uruchamianie: python audyt_23.py --input mecze_test_22.csv --output raporty_23
Brak zależności zewnętrznych.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

OUTCOMES = ("1", "X", "2")
MODEL_PREFIXES = {"2.0": "v20", "2.1": "v21", "2.2 eksperyment": "kal"}


def read_data(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("Pusty plik CSV")
    required = {"league", "season", "match_id", "kickoff_utc", "outcome", "v21_typ", "kal_typ", "v21_brier", "kal_brier"}
    for prefix in MODEL_PREFIXES.values():
        required.update({f"{prefix}_p1", f"{prefix}_px", f"{prefix}_p2"})
    missing = sorted(required - set(rows[0]))
    if missing:
        raise ValueError("Brak kolumn: " + ", ".join(missing))
    seen = set()
    for no, r in enumerate(rows, 2):
        if r["outcome"] not in OUTCOMES:
            raise ValueError(f"Wiersz {no}: niewłaściwy wynik: {r['outcome']}")
        ident = (r["league"], r["season"], r["match_id"])
        if ident in seen:
            raise ValueError(f"Wiersz {no}: zdublowany identyfikator meczu: {ident}")
        seen.add(ident)
        try:
            r["date"] = datetime.fromisoformat(r["kickoff_utc"].replace("Z", "+00:00")).date().isoformat()
        except ValueError as exc:
            raise ValueError(f"Wiersz {no}: błędna data: {r['kickoff_utc']}") from exc
        for prefix in MODEL_PREFIXES.values():
            p = [float(r[f"{prefix}_p1"]), float(r[f"{prefix}_px"]), float(r[f"{prefix}_p2"])]
            if any(not math.isfinite(x) or x < 0 or x > 1 for x in p):
                raise ValueError(f"Wiersz {no}: wartości spoza 0–1 lub NaN: {prefix}")
            if abs(sum(p) - 1) > 0.0001:
                raise ValueError(f"Wiersz {no}: prawdopodobieństwa nie sumują się do 1: {prefix}")
            r[f"{prefix}_probs"] = p
            r[f"{prefix}_typ_calc"] = OUTCOMES[max(range(3), key=lambda i: p[i])]
            r[f"{prefix}_brier_calc"] = sum((p[i] - (1 if r['outcome'] == OUTCOMES[i] else 0))**2 for i in range(3))
            r[f"{prefix}_ll_calc"] = -math.log(max(p[OUTCOMES.index(r["outcome"])], 1e-15))
        for prefix, name in (("v21", "v21"), ("kal", "kal")):
            if r[f"{prefix}_typ_calc"] != r[f"{name}_typ"]:
                raise ValueError(f"Wiersz {no}: niezgodny typ {name} (źródło vs argmax)")
            if abs(r[f"{prefix}_brier_calc"] - float(r[f"{name}_brier"])) > 1e-5:
                raise ValueError(f"Wiersz {no}: niezgodny Brier {name}")
    return rows


def average(values):
    return sum(values)/len(values) if values else 0.0


def metrics(rows, prefix):
    n = len(rows)
    return {
        "liczba_meczow": n,
        "trafnosc": average([r[f"{prefix}_typ_calc"] == r["outcome"] for r in rows]),
        "brier": average([r[f"{prefix}_brier_calc"] for r in rows]),
        "log_loss": average([r[f"{prefix}_ll_calc"] for r in rows]),
        "srednie_p_remisu": average([r[f"{prefix}_probs"][1] for r in rows]),
        "rzeczywisty_odsetek_remisow": average([r["outcome"] == "X" for r in rows]),
        "liczba_typow": dict(Counter({k: sum(r[f"{prefix}_typ_calc"] == k for r in rows) for k in OUTCOMES})),
        "liczba_wynikow": dict(Counter({k: sum(r["outcome"] == k for r in rows) for k in OUTCOMES})),
        "najwyzsze_p_remisu": max(r[f"{prefix}_probs"][1] for r in rows),
        "minimalna_przewaga_nad_p_remisu": min(max(r[f"{prefix}_probs"][0], r[f"{prefix}_probs"][2]) - r[f"{prefix}_probs"][1] for r in rows),
        "sredni_brier_gdy_padl_remis": average([r[f"{prefix}_brier_calc"] for r in rows if r["outcome"] == "X"]),
    }


def quintiles_draw(rows, prefix):
    ranked = sorted(rows, key=lambda r: r[f"{prefix}_probs"][1])
    sections = []
    for k in range(5):
        s = ranked[k * len(rows) // 5 : (k + 1) * len(rows) // 5]
        sections.append({
            "grupa": k+1,
            "liczba": len(s),
            "srednie_p_remisu": average([r[f"{prefix}_probs"][1] for r in s]),
            "odsetek_remisow": average([r["outcome"] == "X" for r in s]),
        })
    return sections


def cluster_bootstrap_diff(rows, prefix_a, prefix_b, n_rep=4000, seed=23):
    """Różnica średniej miary A - B (niżej = lepiej), grupy = dni UTC."""
    daily = defaultdict(list)
    for r in rows:
        daily[r["date"]].append(r[f"{prefix_a}_brier_calc"] - r[f"{prefix_b}_brier_calc"])
    groups = list(daily.values())
    rng = random.Random(seed)
    distribution = []
    for _ in range(n_rep):
        total, count = 0.0, 0
        for __ in range(len(groups)):
            group = groups[rng.randrange(len(groups))]
            total += sum(group)
            count += len(group)
        distribution.append(total/count)
    distribution.sort()
    return [distribution[int(0.025*n_rep)], distribution[int(0.975*n_rep) - 1]]


def cluster_bootstrap_accuracy_vs_home(rows, prefix, n_rep=4000, seed=23):
    daily = defaultdict(list)
    for r in rows:
        daily[r["date"]].append(int(r[f"{prefix}_typ_calc"] == r["outcome"]) - int(r["outcome"] == "1"))
    groups = list(daily.values())
    rng = random.Random(seed)
    distribution = []
    for _ in range(n_rep):
        total, count = 0, 0
        for __ in range(len(groups)):
            group = groups[rng.randrange(len(groups))]
            total += sum(group)
            count += len(group)
        distribution.append(total/count)
    distribution.sort()
    return [distribution[int(0.025*n_rep)], distribution[int(0.975*n_rep)-1]]


def pct(value):
    return f"{100*value:.2f}%"


def report(rows, source):
    by_league = defaultdict(list)
    for r in rows:
        by_league[r["league"]].append(r)
    overall = {name: metrics(rows, prefix) for name, prefix in MODEL_PREFIXES.items()}
    league_scores = {league: {name: metrics(subset, prefix) for name, prefix in MODEL_PREFIXES.items()} for league, subset in sorted(by_league.items())}
    m20, m21, m22 = overall.values()
    brier_gain_20_vs21 = m21["brier"] - m20["brier"]  # >0 oznacza, że 2.0 lepsza
    brier_gain_20_vs22 = m22["brier"] - m20["brier"]
    ci_v20_vs21 = cluster_bootstrap_diff(rows, "v20", "v21")
    ci_v20_vs22 = cluster_bootstrap_diff(rows, "v20", "kal")
    ci_accuracy_vs_home = cluster_bootstrap_accuracy_vs_home(rows, "v21")
    always_home = average([r["outcome"] == "1" for r in rows])
    diagnostics = {
        "typ": "audyt_offline_only",
        "wejscie": str(source),
        "liczba_meczow": len(rows),
        "liczba_dni_meczowych": len(set(r["date"] for r in rows)),
        "od": min(r["kickoff_utc"] for r in rows),
        "do": max(r["kickoff_utc"] for r in rows),
        "walidacja_danych": "OK; unikalne mecze; poprawne 1X2, sumy i zgodne zapisane typy/Brier",
        "metryki": overall,
        "ligi": league_scores,
        "diagnostyka_remisow_wg_kwintyli": {name: quintiles_draw(rows, prefix) for name, prefix in MODEL_PREFIXES.items()},
        "punkt_odniesienia_trafnosc_zawsze_1_na_tescie": always_home,
        "roznica_trafnosci_21_vs_zawsze_1": m21["trafnosc"] - always_home,
        "95ci_roznicy_trafnosci_21_vs_zawsze_1": ci_accuracy_vs_home,
        "brier_20_lepszy_niz_21_o": brier_gain_20_vs21,
        "brier_20_lepszy_niz_22_o": brier_gain_20_vs22,
        "95ci_brier_20_minus_21": ci_v20_vs21,
        "95ci_brier_20_minus_22": ci_v20_vs22,
        "bootstrap": "4000 replik; resampling dni meczowych UTC; przedziały opisowe, nie dowód przewagi",
        "decyzja": "NIE_WDRAZAC_ZMIAN_W_SILNIKU",
        "ograniczenia": [
            "Dane tylko z testu sezonu 2025, a nie niezależny nowy test ex ante",
            "Brak niezależnej weryfikacji, czy wejścia i prognozy istniały przed pierwszym gwizdkiem",
            "Brak kursów bukmacherskich i kosztów, zatem nie wyliczamy ROI",
            "Porównanie z zawsze 1 na tej samej próbce jest opisowe, nie stanowi modelu bazowego dopasowanego na treningu",
            "Brak podstaw do obiecywania opłacalności zakładów lub przewagi nad rynkiem",
        ],
    }
    lines = [
        "# 🫜 RZOTKIEWKA AI — audyt diagnostyczny 2.3",
        "",
        "**Decyzja: NIE PODMIENIAĆ obecnego silnika ani strony.** To wyłącznie audyt offline na historycznym pliku testowym.",
        "",
        f"Plik: `{Path(source).name}`; {len(rows)} meczów w {diagnostics['liczba_dni_meczowych']} dniach meczowych; zakres {diagnostics['od']} — {diagnostics['do']}.",
        "Kontrola danych: **OK** (bez duplikatów; poprawne prawdopodobieństwa i pola kontrolne).",
        "",
        "## Porównanie modeli na tym samym teście",
        "",
        "| Model | Trafność 1X2 | Brier ↓ | Log loss ↓ | Śr. P(X) | Typy X |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, m in overall.items():
        lines.append(f"| {name} | {pct(m['trafnosc'])} | {m['brier']:.5f} | {m['log_loss']:.5f} | {pct(m['srednie_p_remisu'])} | {m['liczba_typow']['X']} |")
    lines.extend([
        "",
        f"**Rzeczywiste remisy:** {m21['liczba_wynikow']['X']}/{len(rows)} = {pct(m21['rzeczywisty_odsetek_remisow'])}.",
        f"**Punkt odniesienia:** zawsze wybierając gospodarzy trafiono by {pct(always_home)}; model 2.1 ma przewagę {100*(m21['trafnosc']-always_home):+.2f} punktu procentowego na tych danych.",
        f"95% przedział bootstrap różnicy trafności 2.1 minus 'zawsze 1': [{100*ci_accuracy_vs_home[0]:+.2f}, {100*ci_accuracy_vs_home[1]:+.2f}] p.p. — nie traktować jako wykazanej przewagi.",
        "",
        "## Co oznacza brak typów X?",
        "",
        "Wybór 1/X/2 jest robiony przez **argmax** (największe z trzech prawdopodobieństw).",
        f"Model 2.1 przypisał remisowi średnio {pct(m21['srednie_p_remisu'])} przy {pct(m21['rzeczywisty_odsetek_remisow'])} faktycznych remisów, ale P(X) nigdy nie była największa.",
        f"Najwyższe P(X) w 2.1: {pct(m21['najwyzsze_p_remisu'])}; najmniejsza przewaga silniejszej prognozy 1/2 nad X: {100*m21['minimalna_przewaga_nad_p_remisu']:.2f} p.p.",
        "Zerowa liczba typów X **nie dowodzi błędu**. Prawdopodobieństwa należy oceniać oddzielnie od klasyfikacji; dodawanie sztucznego bonusu za remis bez walidacji może pogorszyć Brier.",
        "",
        "## Kalibracja remisów — 5 grup o podobnej liczebności (model 2.1)",
        "",
        "| Grupa (od najmniejszego P(X)) | Mecze | Średnie P(X) | Faktyczne remisy |",
        "|---|---:|---:|---:|",
    ])
    for row in diagnostics["diagnostyka_remisow_wg_kwintyli"]["2.1"]:
        lines.append(f"| {row['grupa']} | {row['liczba']} | {pct(row['srednie_p_remisu'])} | {pct(row['odsetek_remisow'])} |")
    lines.extend([
        "",
        "## Wyniki ligowe",
        "",
        "| Liga | Mecze | Brier 2.0 | Brier 2.1 | Brier 2.2 eksperyment | Trafność 2.1 |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for league, mm in league_scores.items():
        lines.append(f"| {league} | {mm['2.1']['liczba_meczow']} | {mm['2.0']['brier']:.5f} | {mm['2.1']['brier']:.5f} | {mm['2.2 eksperyment']['brier']:.5f} | {pct(mm['2.1']['trafnosc'])} |")
    lines.extend([
        "",
        "## Czy 2.0 jest naprawdę lepsza?",
        "",
        f"W teście Brier 2.0 jest mniejszy od 2.1 o **{brier_gain_20_vs21:.5f}** oraz od eksperymentu 2.2 o **{brier_gain_20_vs22:.5f}**.",
        f"Przedział bootstrap Brier(2.0) − Brier(2.1): [{ci_v20_vs21[0]:+.5f}, {ci_v20_vs21[1]:+.5f}].",
        f"Przedział bootstrap Brier(2.0) − Brier(2.2): [{ci_v20_vs22[0]:+.5f}, {ci_v20_vs22[1]:+.5f}].",
        "Oba wyniki to drobne różnice retrospektywne, a nie potwierdzony wzrost jakości. **Nie promujemy żadnej nowej wersji na podstawie tego raportu.**",
        "",
        "## Kolejność prac przed wydaniem 2.3 produkcyjnej",
        "",
        "1. Zapisywać prognozy **przed meczem**, z datą utworzenia, datą spotkania, identyfikatorem modelu i danymi wejściowymi.",
        "2. Rozdzielić ocenę prawdopodobieństw 1/X/2 od pokazywanego użytkownikowi typu.",
        "3. Porównać kilka prostych, z góry ustalonych modeli na kolejnych nowych meczach, bez strojenia na teście.",
        "4. Dopiero po uzyskaniu odpowiednich danych zbierać kursy z chwili prognozy i weryfikować opłacalność po uwzględnieniu kosztów.",
        "5. Przygotować zbieranie opinii czterech testerów strony, bez deklarowania potwierdzonej skuteczności typerskiej.",
        "",
        "**Ograniczenia:** audyt retrospektywny; brak niezależnego potwierdzenia archiwalności wejść do wcześniejszych prognoz, brak kursów i ROI. Wyniki nie dowodzą przewagi nad bukmacherem.",
        "",
    ])
    return diagnostics, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Offline diagnostyka RZOTKIEWKA AI 2.3")
    parser.add_argument("--input", default="mecze_test_22.csv", help="CSV z 2.2")
    parser.add_argument("--output", default="raporty_23", help="Folder raportów")
    args = parser.parse_args()
    source = Path(args.input)
    dest = Path(args.output)
    rows = read_data(source)
    diagnostic, markdown = report(rows, source)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "wyniki_23.json").write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2), encoding="utf-8")
    (dest / "RAPORT_23.md").write_text(markdown, encoding="utf-8")
    print(f"OK: sprawdzono {len(rows)} meczów. Raporty: {dest.resolve()}")
    print(f"Decyzja: {diagnostic['decyzja']}")


if __name__ == "__main__":
    main()

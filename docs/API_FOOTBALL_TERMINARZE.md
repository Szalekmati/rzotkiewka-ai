# RZOTKIEWKA: audyt rzeczywistych terminarzy 7 lig

**NIE jest to zasilanie produkcji ani dowod skutecznosci modelu.**
Publiczne repozytorium **nie przechowuje surowych danych API**; workflow
drukuje wylacznie zagregowane liczniki. Klucz tylko w GitHub Secrets.

Skrypt `api_football_fixtures_quality.py` bada te same 7 lig co katalog
API-FOOTBALL: Premier League 39, LaLiga 140, Bundesliga 78, Serie A 135,
Ligue 1 61, Ekstraklasa 106, Liga Mistrzow UEFA 2.

- `/status` potwierdza aktywny pakiet i minimum 100 zapytan rezerwy.
- Maksymalnie **7 wywolan `/fixtures` na uruchomienie** - jedno na lige.
- Okno maksymalnie 14 dni, nie w przyszlosci i we wskazanym sezonie.
  Domyslnie: ostatnie 10 dni do dzisiaj (UTC).
- Kontrole: liczba rekordow i paginacja, unikalne ID meczow, liga i sezon,
  prawidlowy czas ze strefa, identyfikatory druzyn, koncowe wyniki
  rozegranych meczow oraz opoznione statusy.
- `SCHEMAT_OK` znaczy tylko, ze w badanej probie **nie zidentyfikowano**
  bledow struktury i opoznionych nierozliczonych statusow. Nie oznacza to
  kompletnego sezonu, zgodnosci z niezaleznym zrodlem ani zgody licencyjnej.
- `DO_WERYFIKACJI` = problem lub opozniony nierozliczony status; nie
  przesadza, czy mecz faktycznie zostal rozegrany.
- `PUSTA_PROBA` = brak rekordow w wybranym oknie, a nie brak ligi.
- Testy `pull_request` i `push` sa offline. Produkcyjne API jest
  odpytywane **wylacznie** podczas recznego `workflow_dispatch`
  (poza jednorazowo kontrolowanym audytem z osobnym workflow).
- Nie zmienia to `predictions.json`, `lab_forward/`, strony ani modelu.

Dokumentacja API: https://www.api-football.com/documentation-v3

Przed jakimkolwiek publicznym wyswietlaniem danych dostawcy należy
oddzielnie sprawdzic prawa do wykorzystania komercyjnego.

## Potwierdzony audyt, 11 listopada 2026, 16:36 UTC

Zrodlo: [GitHub Actions #43059898768](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43059898768).
Badane okno: 2026-11-01 do 2026-11-10 (UTC), sezon 2026.

| Liga | ID API | Mecze zakonczone | Uwagi o probie |
|---|---:|---:|---|
| Premier League | 39 | 12 | SCHEMAT_OK |
| LaLiga | 140 | 15 | SCHEMAT_OK |
| Bundesliga | 78 | 11 | SCHEMAT_OK |
| Serie A | 135 | 17 | SCHEMAT_OK |
| Ligue 1 | 61 | 14 | SCHEMAT_OK |
| Ekstraklasa | 106 | 12 | SCHEMAT_OK |
| Liga Mistrzow UEFA | 2 | 18 | SCHEMAT_OK |
| **Razem** | | **99** | **0 wykrytych bledow strukturalnych** |

- Wszystkie 99 rekordow w badanej probie mialy status finalny i niepuste wyniki.
- Zero wykrytych: duplikatow ID, bledow ligi/sezonu, niepoprawnych
  dat ze strefa, brakujacych ID/nazw druzyn, brakujacych wynikow koncowych,
  nierozpoznanych statusow lub opoznionych nierozliczonych rekordow.
- Testy offline: **10/10**. Status PRO potwierdzony przed proba.
  Licznik statusu API przed odczytem wynosil 2; probka korzystala maksymalnie
  z 7 kolejnych zapytan (po 1 na lige) w ramach juz oplaconego planu.
- Nie zebrano statystyk szczegolowych, skladu, kursow ani historycznych
  trendow formy. Nie rozstrzygnieto praw do publikacji danych.
- **To nie jest walidacja pojedynczych wynikow wobec niezaleznego zrodla,
  potwierdzenie pelnego sezonu ani test jakosci predykcji.**
- Po audycie usunieto jednorazowy wyzwalacz. Rekomendacja: nastepnie
  sprawdzic porownanie wynikow i dat z niezaleznym zrodlem, dopasowanie
  identyfikatorow zespolow, a dopiero potem odseparowany backtest.

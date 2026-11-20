# RZOTKIEWKA AI — ręczny przegląd referencji UEFA 2026/27

**Data przeglądu:** 15 listopada 2026. **Zakres:** wyłącznie dane odniesienia w roboczej gałęzi PR #46, bez produkcji i bez pobierania meczów z OpenLigaDB.

## Dane źródłowe

- UEFA, [2026/27 Champions League: All the league phase fixtures and results](https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-uefa-champions-league-all-the-league-phase-fixtures-a/), opublikowany/zaktualizowany 4.11.2026.
- Kod referencyjny: `research/ucl_official_matchday5.js` (`official` + `officialRemaining`, razem 72 wpisy).
- Porównano kolejno pary gospodarze/goście, dni i godziny z widocznym wykazem UEFA. UEFA podaje czasy CET; w kodzie 18:45 CET = 17:45 UTC, 21:00 CET = 20:00 UTC.

| Kolejka | Data | Liczba sprawdzonych pozycji | Weryfikacja listy referencyjnej |
|---|---|---:|---|
| 5 | 24.11.2026 | 9 | 9/9 zgodnych |
| 5 | 25.11.2026 | 9 | 9/9 zgodnych |
| 6 | 08.12.2026 | 9 | 9/9 zgodnych |
| 6 | 09.12.2026 | 9 | 9/9 zgodnych |
| 7 | 19.01.2027 | 9 | 9/9 zgodnych |
| 7 | 20.01.2027 | 9 | 9/9 zgodnych |
| 8 | 27.01.2027 | 18 | 18/18 zgodnych |
| **Razem** | | **72** | **72/72 zgodnych z datowanym tekstem UEFA** |

## Granice tego wyniku

**To nie jest 72/72 aktualnie dopasowanych meczów OpenLigaDB!** Próba odczytania publicznego endpointu `https://api.openligadb.de/getmatchdata/ucl/2026` z bieżącego środowiska nie udostępniła odpowiedzi do analizy. Nie potwierdzono więc żadnych aktualnych ID meczów/drużyn u dostawcy, kompletności jego wyników, ewentualnych zmian terminarza od 4.11, zgodności dalszych faz ani prawa do komercyjnej redystrybucji danych.

Wykaz UEFA jest dokumentem z 4 listopada i wymaga ponownego porównania, jeśli terminy zostaną zaktualizowane. Kontrole `verifyAllUpcoming` i `UclPreview.inspect` nadal blokują niezweryfikowane, dodatkowe lub niespójne wpisy. Zielony test offline oznacza wyłącznie poprawność testowanych reguł.

**Status publikacji:** STOP. Nie zmieniać `index.html`, `predictions.json`, LAB, GitHub Pages, DNS, Premium ani płatnych usług. Przed dopuszczeniem do strony: pobrać realny zestaw OpenLigaDB, wykonać kontrolę rekord po rekordzie względem aktualnej oficjalnej listy, sprawdzić licencję i udokumentować niezależną zgodę na wydanie.

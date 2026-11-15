# RZOTKIEWKA AI — prototyp wspólnego cache dla trzech lig niemieckich

**Status:** RESEARCH_ONLY / draft, 15.11.2026. Tylko lokalna praca na trzech istniejących plikach JSON. Brak sieci, automatycznego pobierania, publikacji, zmian LAB, modeli, Pages, Premium i płatnych usług.

## Cel

Trzy już podłączone ligi OpenLigaDB: `bl1` (Bundesliga), `bl2` (2. Bundesliga), `bl3` (3. Liga), sezon 2026/27. Przyszły system będzie mógł odczytać raz dane źródłowe i wystawić wielu użytkownikom jeden kontrolowany snapshot. Na razie jest to **niepodłączony prototyp**, a nie nowy LIVE feed.

## Pliki

- `research/german_fixture_bundle.cjs`: odczyt **trzech wskazanych plików lokalnych** i bezpieczna transformacja do jednego minimalnego badawczego JSON. Nie odpytuje OpenLigaDB.
- `tests/test_german_fixture_bundle.cjs`: testy syntetyczne offline (bez kluczy i płatnych usług).
- Zmodyfikowany istniejący `.github/workflows/audyt_nowych_lig.yml` uruchamia te testy przy PR i nie dodaje nowego harmonogramu.

Przykład, wyłącznie po przygotowaniu **autentycznych** trzech plików ze źródła:
```sh
node research/german_fixture_bundle.cjs --bl1 /tmp/bl1-2026.json --bl2 /tmp/bl2-2026.json --bl3 /tmp/bl3-2026.json --output /tmp/german-2026.research.json
```
Ostrzeżenie: przykład nie pobiera żadnych danych; ścieżki są przykładowe. Plik wyjściowy wymaga końcówki `.research.json`, powstaje wyłącznie przy braku wszystkich błędów i **nigdy nie jest nadpisywany**.

## Reguły fail-closed

- Wszystkie trzy ligi i sezon 2026, spójny `leagueId` wewnątrz każdej ligi, różne `leagueId` między ligami; brak lub sprzeczność oznacza STOP.
- ID meczu i klubu, spójne nazwy, jawne UTC, daty lipiec 2026–czerwiec 2027, limit rekordów, brak duplikatów, jedna para gospodarze-goście w sezonie, jawne flagi meczu.
- Zakończony mecz musi mieć jednoznaczny wynik końcowy, przyszły nie może mieć wyniku; spotkanie starsze niż 48 h bez końcowego wyniku blokuje cały zestaw.
- Co najmniej jedno przyszłe spotkanie każdej ligi, ale to **nie dowodzi kompletności sezonu**.
- Usuwane są herby, URL-e i zbędne pola surowego źródła; wynik zawiera jedynie przyszłe spotkania, znaczniki pochodzenia i datę odczytu.
- Po sześciu godzinach snapshot jest oznaczany jako nieważny. SHA-256 wykrywa przypadkową zmianę, **nie jest podpisem bezpieczeństwa ani potwierdzeniem pochodzenia**.

## Przed jakimkolwiek wdrożeniem

- [ ] Rzeczywista kontrola trzech odpowiedzi OpenLigaDB, danych historycznych, niezależnego terminarza i praw licencyjnych.
- [ ] Audyt zgodności formatu, identyfikatorów i wyników, również przy przesuniętych meczach.
- [ ] Osobny projekt centralnego pobierania w już istniejących limitach GitHub Actions (bez zwiększania harmonogramu bez zgody).
- [ ] Podgląd mobilny i plan rollback dla strony, zachowanie zamrożonych LAB 2.1/2.2.
- [ ] Osobna decyzja o wdrożeniu po pozytywnym audycie, bez mieszania research z prognozami lub Premium.

**Brak automatycznego przejścia do produkcji.** Zielone testy offline oznaczają jedynie, że testowane reguły kodu działają.

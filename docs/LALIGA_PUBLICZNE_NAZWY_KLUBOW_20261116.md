# LaLiga 2026/27 — kontrola nazw OpenFootball i listy oficjalnej (16.11.2026)

**Status:** `RESEARCH_ONLY` / `ID_NOT_VERIFIED`. Wyłącznie publiczne nazwy, bez wywołań płatnego API i bez dopuszczania lig, aliasów czy wyników.

## Źródła i metoda

1. Publiczne archiwum OpenFootball przypięte do SHA: https://github.com/openfootball/espana/blob/80035a93dd4920985af52aa097a54a6fb888563b/2026-27/1-liga.txt
2. Oficjalne wykazy klubów LaLiga 2026/27: https://www.laliga.com/en-US/laliga-easports/clubs
3. Wersjonowany oficjalny wykaz w RZOTKIEWKA: `api_football_official_roster.py`, `OFFICIAL[140]["clubs"]`.
4. Rejestr stanu dopuszczenia ID: `data/identity_release_registry.json`.

Wydobyto unikatowe nazwy klubów z publicznych rekordów archiwum bez kopiowania meczów/wyników. Normalizacja *podstawowa*: Unicode NFKD, małe litery, `&`→`and`, usunięcie skrajnego `FC`, `CF`, `AFC` (nie modyfikuje `RC`, `R.`, `Real`, `Club`, `de`, `Santander`, `La Coruña` itd.). Parę liczymy jako dopasowaną **wyłącznie przy identycznym ciągu po normalizacji**. To nie jest zatwierdzenie relacji tożsamości klubu lub provider ID.

## Wynik ścisłego porównania

- Archiwum OpenFootball: **20 unikatowych nazw**.
- Oficjalna lista: **20 unikatowych klubów**.
- Zgodność ścisła po podstawowej normalizacji: **13/20**.
- Różne warianty bez ścisłej zgodności: **7/20**. *Żaden z nich nie jest automatycznie zatwierdzony ani produkcyjnym aliasem.*
- Niezależnie zweryfikowane `provider_team_id` (LaLiga): **0/11** kandydatów API-Football. Odrębne **11** zgłoszeń API nie jest tożsame z poniższymi siedmioma wariantami publicznych nazw.

### Nazwy 13/20 dopasowane bez dodatkowych reguł

| Nazwa w OpenFootball | Oficjalna nazwa |
| --- | --- |
| Athletic Club | Athletic Club |
| CA Osasuna | CA Osasuna |
| Deportivo Alavés | Deportivo Alavés |
| Elche CF | Elche CF |
| FC Barcelona | FC Barcelona |
| Getafe CF | Getafe CF |
| Levante UD | Levante UD |
| Málaga CF | Málaga CF |
| RCD Espanyol de Barcelona | RCD Espanyol de Barcelona |
| Real Madrid CF | Real Madrid |
| Sevilla FC | Sevilla FC |
| Valencia CF | Valencia CF |
| Villarreal CF | Villarreal CF |

### Siedem **propozycji** do ręcznego potwierdzenia

W drugiej kolumnie podano wyłącznie orientacyjną nazwę oficjalną na podstawie podobieństwa słownego i składu rozgrywek. **Nie weryfikowano oficjalnego potwierdzenia wariantu ani team ID.** Kolumna nie jest zatwierdzonym słownikiem.

| Wariant OpenFootball | Możliwa oficjalna nazwa do sprawdzenia | Status |
| --- | --- | --- |
| Club Atlético de Madrid | Atlético de Madrid | DO WERYFIKACJI — niezatwierdzona propozycja nazw |
| Rayo Vallecano de Madrid | Rayo Vallecano | DO WERYFIKACJI — niezatwierdzona propozycja nazw |
| RC Celta de Vigo | Celta | DO WERYFIKACJI — niezatwierdzona propozycja nazw |
| RC Deportivo La Coruña | RC Deportivo | DO WERYFIKACJI — niezatwierdzona propozycja nazw |
| Real Betis Balompié | Real Betis | DO WERYFIKACJI — niezatwierdzona propozycja nazw |
| Real Racing Club de Santander | R. Racing Club | DO WERYFIKACJI — niezatwierdzona propozycja nazw |
| Real Sociedad de Fútbol | Real Sociedad | DO WERYFIKACJI — niezatwierdzona propozycja nazw |

### Ryzyka szczególne

- `RC Deportivo La Coruña` wymaga osobnego odczytu oficjalnych źródeł klubu i ligi, bo w wykazie jest również `Deportivo Alavés`. Nigdy nie mapować samego `Deportivo` bez dodatkowego kontekstu.
- `Real Racing Club de Santander` i `R. Racing Club` nie powinny być łączone na podstawie samych skrótów `R.` / `Real`.
- Każda z siedmiu pozycji wymaga strony konkretnego klubu lub oficjalnego potwierdzenia wariantu. Dopiero potem można uznać *zgodność nazw*, **nadal nie tożsamość konkretnego API provider ID**.
- Zgodność 20 uczestników w dwóch listach nie potwierdza poprawności terminarzy, końcowych wyników, licencji ani skuteczności prognoz. Znane problemy feedu `la1/2026` (kluby z innych lig) pozostają niezamknięte.

**Bramka produkcji: STOP.** Bez wpisu do zatwierdzonych map ID, bez zmiany `data/identity_release_registry.json`, bez `release.requested`, bez zmian w `main`, Pages, prognozach, LAB i kosztach.

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
- Różne warianty bez ścisłej zgodności: **7/20**. Wszystkie siedem ma teraz odrębny dowód publicznego nazewnictwa w tabeli niżej; żaden nie został automatycznie zatwierdzony ani nie jest produkcyjnym aliasem.
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

### Wynik dodatkowego odczytu oficjalnych źródeł: siedem wariantów (16.11.2026)

W pierwszej kontroli **13/20** nazw było dokładnie zgodnych po podstawowej normalizacji, a **7/20** wymagało osobnej weryfikacji. Dodatkowo sprawdzono **każdą z tych siedmiu par** w publicznych profilach LaLiga lub własnych komunikatach klubów. Oficjalne źródła **wspierają tożsamość nazw tych samych klubów** w siedmiu przypadkach; nie oznacza to dopuszczenia aliasów API ani mapy identyfikatorów `provider_team_id`.

| Wariant w archiwum OpenFootball | Nazwa ligowa | Potwierdzenie nazewnictwa w źródle klubu / LaLiga | Ocena |
| --- | --- | --- | --- |
| Club Atlético de Madrid | Atlético de Madrid | [Profil LaLiga](https://www.laliga.com/clubes/atletico-de-madrid) i [nota prawna klubu](https://www.atleticodemadrid.com/atm/aviso-legal) podają pełną nazwę Club Atlético de Madrid | Wariant nazwy wsparty publicznie |
| Rayo Vallecano de Madrid | Rayo Vallecano | [Profil LaLiga](https://www.laliga.com/clubes/rayo-vallecano) łączy etykietę Rayo Vallecano z pełnym Rayo Vallecano de Madrid SAD | Wariant nazwy wsparty publicznie |
| RC Celta de Vigo | Celta | [Oficjalna informacja klubu o rebrandingu](https://rccelta.es/en/club/actualidad/celta-presents-its-new-brand-more-essence-more-identity-more-ours/) wymienia Celta, Real Club Celta, Celta de Vigo i RC Celta jako akceptowane formy; [nota prawna](https://rccelta.es/en/aviso-legal/) podaje Real Club Celta de Vigo | Wariant nazwy wsparty publicznie |
| RC Deportivo La Coruña | RC Deportivo | [Profil LaLiga](https://www.laliga.com/clubes/rc-deportivo) wskazuje Real Club Deportivo de A Coruña; [decyzja klubu z 23.06.2026](https://www.rcdeportivo.es/es/noticias/la-junta-general-extraordinaria-del-rc-deportivo-aprueba-la-adecuacion-de-su-denominacion-social) wyjaśnia zmianę La Coruña → A Coruña | Wariant historyczny wsparty publicznie |
| Real Betis Balompié | Real Betis | [Profil LaLiga](https://www.laliga.com/clubes/real-betis) pokazuje etykietę Real Betis i pełną nazwę Real Betis Balompié SAD | Wariant nazwy wsparty publicznie |
| Real Racing Club de Santander | R. Racing Club | [Profil LaLiga](https://www.laliga.com/clubes/r-racing-club) łączy skrót R. Racing Club z Real Racing Club de Santander; [strona klubu](https://www.realracingclub.es/el-club) podaje pełną nazwę | Wariant nazwy wsparty publicznie |
| Real Sociedad de Fútbol | Real Sociedad | [Profil LaLiga](https://www.laliga.com/clubes/real-sociedad) pokazuje obie formy; [oficjalna informacja prawna](https://www.realsociedad.eus/es/i/te-escuchamos/aviso-legal) podaje pełną nazwę | Wariant nazwy wsparty publicznie |

**Podsumowanie tylko dla publicznych nazw:** 13/20 zgodne wprost po podstawowej normalizacji, pozostałe 7/20 wspierane odrębnymi stronami klubów/ligi. **Żaden z siedmiu wpisów nie jest aliasem wdrożonym do aplikacji ani potwierdzeniem identyfikatorów API.** Wciąż **0/11** niezależnie zweryfikowanych map ID w LaLiga i **0/17** w dwóch badanych ligach.

### Ryzyka szczególne

- `RC Deportivo La Coruña` ma publicznie udokumentowaną zmianę nazwy na `A Coruña`, ale w tej samej lidze występuje także `Deportivo Alavés`. Nigdy nie mapować samego `Deportivo` bez dodatkowego kontekstu.
- `Real Racing Club de Santander` i `R. Racing Club` zostały powiązane przez konkretne źródła klubu i ligi, a nie przez same skróty `R.` / `Real`.
- Każdy z siedmiu wariantów ma odsyłacz do konkretnego oficjalnego źródła **dla nazwy**. **Żadne z tych źródeł nie weryfikuje konkretnego team ID API-Football**. Brak prawa do autozatwierdzania mapy `provider_team_id`.
- Zgodność 20 uczestników w dwóch listach nie potwierdza poprawności terminarzy, końcowych wyników, licencji ani skuteczności prognoz. Znane problemy feedu `la1/2026` (kluby z innych lig) pozostają niezamknięte.

**Bramka produkcji: STOP.** Bez wpisu do zatwierdzonych map ID, bez zmiany `data/identity_release_registry.json`, bez `release.requested`, bez zmian w `main`, Pages, prognozach, LAB i kosztach.

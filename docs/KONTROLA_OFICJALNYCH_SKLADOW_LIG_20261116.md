# 🫜 RZOTKIEWKA AI — niezależna kontrola oficjalnych uczestników lig (16.11.2026)

**Tryb:** RESEARCH_ONLY / bez publikacji nowych lig / bez automatycznego zatwierdzania aliasów lub identyfikatorów klubów.

## Co zweryfikowano

Porównano dokładne etykiety 20 klubów w rejestrze `OFFICIAL` w `api_football_official_roster.py` na gałęzi `main` ze źródłami oficjalnymi odczytanymi 16.11.2026:

- Premier League 2026/27: https://www.premierleague.com/en/news/4365156 — **20/20 dokładnych nazw**, bez braków, nadmiarowych nazw i duplikatów.
- LaLiga EA SPORTS 2026/27: https://www.laliga.com/laliga-easports/clubes — **20/20 dokładnych nazw**, bez braków, nadmiarowych nazw i duplikatów.

To jest kontrola **listy nazw i uczestnictwa w sezonie**, a nie kontrola identyfikatorów `team_id`, wyników, terminarzy, licencji ani wydajności modelu.

## Wynik i ograniczenia

| Bramka | Premier League | LaLiga |
| --- | --- | --- |
| Oficjalny wykaz 20 uczestników znaleziony | TAK | TAK |
| Nazwy w lokalnym `OFFICIAL` zgodne literalnie z wykazem | 20/20 | 20/20 |
| Potwierdzone mapy API-Football `team_id -> klub` | **NIE** | **NIE** |
| Wszystkie 17 kandydatów aliasów zweryfikowane indywidualnie | **NIE** | **NIE** |
| Niezależna kontrola pełnych terminarzy / wyników | **NIE** | **NIE** |
| Dopuszczenie do produkcyjnych prognoz 1X2 | **STOP** | **STOP** |

**Następny wymagany dowód:** dla każdego z 17 kandydatów zebrać potwierdzenie (liga, sezon, źródło i numer `team_id`, nazwa w obu źródłach, właściwy klub na oficjalnej liście, identyfikator lub link oficjalnej karty klubu). W razie niejednoznaczności lub braku zgody nie zatwierdzać mapy.

**Szczególna uwaga:** wcześniejsze badania `ucl/2026` wskazały `teamId=356` jako Excelsior Rotterdam przy terminach Barcelony według UEFA. Nie wolno zamienić tego ID w alias Barcelony, nawet jeśli data i wynik są zgodne. Źródło oficjalne: https://www.uefa.com/uefachampionsleague/clubs/50080/matches/ .

## Granice operacyjne

Nie dotyczy działania `index.html`, `predictions.json`, `tips.json`, `lab_forward/`, produkcyjnej wersji modelu, DNS, GitHub Pages, cennika, workflow harmonogramów ani płatności. Nie wykonano żadnych wywołań płatnego API-Football. Werdykt dla nowych lig: **RESEARCH_ONLY / STOP do czasu weryfikacji team-ID i jakości meczów**.

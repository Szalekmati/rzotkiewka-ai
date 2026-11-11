# RZOTKIEWKA AI — dostępność danych przedmeczowych z API-FOOTBALL

Celem jest **ocena danych**, bez nowych prognoz czy zatwierdzenia lig.
Ten audyt celowo nie zmienia działającego silnika ani LAB 2.1/2.2.

## Dane i okna czasowe

- Dwie ligi: Premier League (39) i LaLiga (140), sezon 2026/27.
- Pobieramy komplet endpointu `/fixtures?league=...&season=2026`
  osobno dla obu lig. Łącznie maks. **2 zapytania** z opłaconego
  limitu API-FOOTBALL, po odczycie statusu konta. Brak kosztów nowych usług.
- Weryfikujemy niepowtarzalne ID meczów, dokładną ligę i sezon,
  rozpoznawalną strefę czasu, ID przeciwników, poprawność wyników
  tylko dla statusów `FT/AET` i kompletność odpowiedzi.
- Mecze live, przełożone, anulowane, bez wyniku nie trafiają
  do bazy zakończonych meczów.
- Historyczne wyniki liczymy tylko, jeśli mecz zakończył się według
  statusu API i kickoff był minimum **3 h przed chwilą kontroli**.
  To zachowawcze zabezpieczenie, nie dowód faktycznej godziny
  opublikowania wyniku przez dostawcę.
- Przyszłe mecze to wyłącznie `NS/TBD` z kickoffem późniejszym od
  kontroli, a do okna modelu kwalifikują się terminy 2 h – 8 dni.
- Sprawdzamy aktualne progi produkcyjnego `forecast_engine.py`:
  minimum 24 wyników ligi oraz 4 zakończone mecze na zespół.
  Używamy istniejących funkcji `prior_history` i `team_recent`.
- **Żadnych obliczonych typów, prawdopodobieństw, kursów ani porad
  bukmacherskich.** Nie zapisujemy i nie publikujemy meczów ani
  nazw, ID drużyn, surowych odpowiedzi API czy tokenu.
- Pokazujemy zagregowane: liczbę rekordów, kompletnych dawnych wyników,
  zaplanowanych spotkań, liczbę potencjalnych spotkań w oknie i tych
  z wystarczającą historią do dalszego, oddzielnego badania.

## Interpretacja

`DANE_WYSTARCZAJA_DO_BADANIA` nie oznacza, że dane były faktycznie
dostępne w momencie dawnych spotkań (brak as-of snapshots), że model
jest skuteczny czy że mamy prawo publikować surowe dane dostawcy.
To tylko odpowiedź, czy silnik posiada ilościowo wystarczającą historię
**na moment uruchomienia**. Dalsze dopuszczenie nowych lig wymaga
oddzielnej bramki `club_identity_release_gate.py`, niezależnej kontroli
praw do komercyjnego użycia i prospektywnego testu modeli.

Workflow `api_football_prematch_readiness.yml`: PR i push wykonują
**wyłącznie testy offline**. Żądania z kluczem są wykonywane tylko
po ręcznym `workflow_dispatch`. Żadnych harmonogramów i nowych kosztów.

`predictions.json`, `lab_forward/`, `forecast_engine.py`,
`index.html` i LAB 2.1/2.2 pozostają nietknięte.

## Raport realnego uruchomienia — 11 listopada 2026, 17:44 UTC

[GitHub Actions — kontrolowany audyt](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43070986881).

Stan odczytu na `2026-11-11T17:44:07Z`, sezon 2026/27.

| Metryka | Premier League ID 39 | LaLiga ID 140 |
|---|---:|---:|
| Rekordy spotkan w sezonie | 380 | 380 |
| Rozliczone spotkania z koncowym wynikiem i min. 3 h od rozpoczecia | 100 | 119 |
| Przyszle mecze ze statusem `NS/TBD` | 280 | 260 |
| Mecze o kickoffie w oknie modelu 2 h – 8 dni | 0 | 0 |
| W tym: wystarczajaca historia wedlug progow silnika | 0 | 0 |
| Niekompletne finalne wyniki | 0 | 0 |
| Statusy inne niz `FT/AET` i `NS/TBD` | 0 | 1 |
| Finalne mecze datowane po momencie odczytu | 0 | 0 |
| Faktyczne prognozy utworzone | **0** | **0** |

- Testy offline: **12/12**. Zadanie GitHub Actions: `success`.
- Przed odczytem `/status`: 29/7500 zapytan z opłaconego pakietu PRO.
  Wykonano **dwa** zapytania `/fixtures` (po jednym na lige).
- Zwrócone rekordy przechodzily krytyczne kontrole unikatowosci
  identyfikatorow, stref czasu, ligi i sezonu; wszystkie zakończone
  w badanej odpowiedzi mialy wyniki. Jeden rekord LaLigi mial status
  inny niz finalny albo przyszly `NS/TBD` i nie zostal zaliczony do historii.
- **Brak spotkan w 8-dniowym oknie nie jest bledem integracji**, ale
  oznacza brak podstaw do nowych prognoz na moment testu.
- Nastepny etap: powtorzyc badanie, kiedy pojawia sie realne spotkania
  w oknie; oddzielnie sprawdzic dostepnosc dokladnych timestampow
  publikacji danych i pozniej prospektywne testy modelu.
- Uwaga: samo pokazanie przez API wyniku z przeszlosci nie dowodzi,
  kiedy dane byly faktycznie dostepne. To nie jest dowod skutecznosci
  prognoz ani zgoda na dystrybucje.
- Po wykonaniu jednorazowy wyzwalacz usunieto z repo.
  Reczny, wylacznie na zyczenie workflow pozostaje dostepny.
- Ani LAB 2.1/2.2, ani `predictions.json`, ani strona
  oraz produkcyjny silnik prognoz nie zostaly zmienione.

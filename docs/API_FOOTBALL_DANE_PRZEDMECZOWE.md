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

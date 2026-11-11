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

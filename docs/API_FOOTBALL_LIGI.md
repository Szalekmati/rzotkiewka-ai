# RZOTKIEWKA - audyt 7 lig API-FOOTBALL

To narzedzie do **wewnetrznej oceny metadanych**, a nie wdrozenie kolejnych
lig do przewidywania meczow. Repozytorium publiczne nie przechowuje
odpowiedzi API ani prywatnego klucza.

Siedem kandydatow: Premier League (39), LaLiga (140), Bundesliga (78),
Serie A (135), Ligue 1 (61), Ekstraklasa (106), Liga Mistrzow UEFA (2).
Identyfikatory i dostepnosc sezonu sa weryfikowane poprzez realne API,
a nie automatycznie akceptowane na podstawie nazwy w konfiguracji.

**Workflow:** `.github/workflows/api_football_catalog.yml`, wylacznie
`workflow_dispatch`, domyslnie sezon 2026. Jeden endpoint `/status`
(przed pobraniem, bez obciazania limitu wg dostawcy), jedno zapytanie
`/leagues?season=2026` (z limitu planu). Odmawia wykonania przy
mniej niz 101 wolnych wywolaniach, nie eksportuje danych do plikow.

W logu: liczba rekordow katalogu, zidentyfikowane ligi, deklarowane flagi
pokrycia: `T` = true, `N` = false, `?` = brak wiarygodnej informacji.
**Obecnosc ligi i flagi nie gwarantuja historycznych wynikow, terminow,
kompletnosci statystyk, praw do logo, publikacji danych ani jakości prognoz.**

Kolejne etapy: kontrolowana probka terminarza, dopasowanie ID druzyn,
sprawdzenie wynikow z niezaleznym zrodlem, audyt modelu offline.
Dopiero po zatwierdzeniu mozna projektowac rozszerzenie produkcji.

Regulamin dostawcy zastrzega, ze nie udziela automatycznie licencji
na publiczne rozpowszechnianie danych: https://api-sports.io/terms

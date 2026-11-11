# API-FOOTBALL PRO — bezpieczny test integracji

RZOTKIEWKA posiada obecnie oddzielny produkcyjny silnik OpenLigaDB i zamrozony LAB 2.1/2.2.
Ten etap **nie zmienia** `predictions.json`, `lab_forward/`, publicznej strony ani
modeli. Nie wlacza harmonogramu ani zadnej dodatkowej platnej uslugi.

1. W ustawieniach repozytorium dodaj sekret typu **Actions repository secret** o
   nazwie `API_FOOTBALL_KEY`. Nigdy nie wklejaj go do pliku ani wiadomosci.
2. W GitHub Actions otworz
   **RZOTKIEWKA - test polaczenia API-FOOTBALL PRO**.
3. Kliknij **Run workflow**, ustaw `mode: status`. Odczyt `/status` nie zuzywa
   dziennego limitu wedlug dokumentacji dostawcy. Wynik zawiera tylko
   nazwe planu i liczniki, bez danych konta i klucza.
4. Dopiero po udanym teście mozna uruchomic `mode: fixtures`.
   To **jedno** zapytanie do `/fixtures` (zuzywa limit), domyslnie
   Premier League ID 39, sezon 2026, dzien biezacy UTC. Pusta odpowiedz
   w dniu bez meczu jest prawidlowym rezultatem.
5. Zanim wykorzystamy dane do prognoz lub platnej strony, oddzielnie
   zweryfikujemy jakosc, dopasowanie ID, aktualnosc oraz warunki licencji.

API: `https://v3.football.api-sports.io/`, naglowek `x-apisports-key`.
Nie wykonujemy zapytan po stronie publicznej przegladarki: klucz ma zostac
tylko w serwerowym GitHub Actions. W razie wycieku natychmiast zmien klucz.

# RZOTKIEWKA: niezalezne porownanie wynikow 2026/27

Badanie 2 lig: Premier League i LaLiga (API-FOOTBALL oraz OpenFootball).
Repozytoria OpenFootball deklaruja CC0, ale kwestia praw do wkładow
zewnetrznych i komercyjnej publikacji wymaga dalszej analizy.

Weryfikujemy **wczesne** wyniki sezonu 2026/27, bo dostepne pliki
OpenFootball sa przypiete do commitow z 15 pazdziernika 2026.
Nie wykorzystujemy ich do walidacji listopadowych 99 meczow.

Zrodla archiwalne (przypiete):
- [Premier League](https://github.com/openfootball/england/blob/9ee7a0c351805c99cc334478a9bf04b7d0432fec/2026-27/1-premierleague.txt)
- [LaLiga](https://github.com/openfootball/espana/blob/80035a93dd4920985af52aa097a54a6fb888563b/2026-27/1-liga.txt)

Mechanizm:
- nazywamy drużyny konserwatywnie (usuniecie tylko prefiksu/sufiksu FC/CF/AFC);
- nie dokonujemy dopasowania "podobnych" klubow przez zgadywanie;
- do parowania potrzebujemy identycznej znormalizowanej pary gospodarz/gosc,
  jednoznacznosci i roznicy dat maks. 1 dzien (kalendarz UTC vs lokalna data);
- wyniki porownujemy jako liczby goli; niedopasowanych nie traktujemy jako
  potwierdzone niezgodnosci;
- brak weryfikacji zewnetrznego znacznika czasu archiwum i jego pochodzenia;
  zgodnosc 2 plikow nie oznacza sprawdzenia prawdziwosci calego sezonu.

Workflow `api_football_crosscheck.yml`: PR/push testy offline,
jedynie reczny workflow_dispatch robi maksymalnie 2 odczyty /fixtures.
Brak modyfikacji produkcji, LAB 2.1/2.2, publicznej strony i danych prognoz.
Brak zapisu konkretnych wynikow, nazw meczow i surowej odpowiedzi API.

Wynik uruchomienia musi osobno podac: dopasowane pary, zgodne wyniki,
rozbieznosci, korekty dat, nierozpoznane nazwy oraz dane niepelne.
Nie stanowi walidacji modelu ani prawa do komercyjnej publikacji.

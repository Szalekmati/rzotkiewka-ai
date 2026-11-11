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

## Wynik rzeczywistego testu (11.11.2026, 16:42 UTC)

[GitHub Actions: porownanie dwoch zrodel](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43060940735)

Okno: **21–31 sierpnia 2026**, sezon 2026/27. W kazdym z dwoch
odrebnych zrodel stwierdzono po 43 mecze w badanych rozgrywkach:
Premier League 20 i LaLiga 23.

| Liga | Wyniki OpenFootball | Wyniki API | Dopasowane | Zgodne | Niezgodne | Niedopasowane na zrodlo |
|---|---:|---:|---:|---:|---:|---:|
| Premier League | 20 | 20 | 9 | 9 | 0 | 11 |
| LaLiga | 23 | 23 | 4 | 4 | 0 | 19 |
| **Razem** | **43** | **43** | **13** | **13** | **0** | **30** |

- Przesuniecia dni w dopasowanych parach: **0**.
- Niejednoznaczne dopasowania: **0**.
- Przeszly **9/9 testow offline**.
- Wykonano **maksymalnie 2 zapytania /fixtures** w juz oplaconym PRO;
  przed uruchomieniem `/status` pokazal wykorzystanie 9 zapytan z 7500.
- **13/13 zgodnych oznacza zgodnosc TYLKO tych 13 dopasowanych rekordow**.
  Pozostalych 30 nie mozna nazwac zgodnymi ani sprzecznymi: rozne nazwy
  druzyn, przesuniecia meczow i niezgodny terminarz sa do zbadania.
- Nie wystawia to pozytywnej oceny wszystkim 43 meczom ani 99 meczom
  z listopadowego audytu; ten stary, przypiety snapshot NIE zawiera
  aktualnej historii listopadowej.
- Nie ma jeszcze mapowania identyfikatorow klubow, testu kompletnosci
  dwoch sezonow, weryfikacji licencji, ani zatwierdzonego backtestu.
- Po sukcesie usunieto jednorazowy trigger. Zachowano jedynie
  reczny workflow `api_football_crosscheck.yml` i testy offline.
- `predictions.json`, `lab_forward/`, modele produkcyjne i strona
  nie byly modyfikowane.

**Wniosek:** kolejnym etapem jest jawna, recznie sprawdzona tabela aliasow
nazw dla par 2026/27, druga niezalezna kontrola dat i wynikow, a dopiero
pozniej rozdzielny backtest. Nie dopuszczamy zadnej ligi do produkcji
automatycznie.

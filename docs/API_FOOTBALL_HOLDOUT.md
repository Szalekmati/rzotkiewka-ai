# RZOTKIEWKA – sprawdzenie kandydatow klubow na odrebnej probie

## Dlaczego potrzebny test holdout?
Raport 43/43 z sierpnia 2026 opiera się na meczach wykorzystanych
jednoczesnie do przygotowania 17 **niezatwierdzonych** aliasow klubow.
Nie dowodzi to przenoszenia mapowan na inne mecze. Ten audyt wyklucza
dobieranie nowych nazw na podstawie danych z okresu kontrolnego.

## Zamrozony protokol
- Zrodla: tylko Premier League (ID 39) i LaLiga (ID 140), sezon 2026/27.
- **Uczenie propozycji nazw:** 21–31 sierpnia 2026.
- **Nieznana proba kontrolna:** 4–14 wrzesnia 2026.
- Uczenie tylko na unikatowych nazwach klubow z pierwszego okresu.
  Rozklady bramek i wyniki nie sa uzywane do budowy aliasow.
- Dopasowanie meczow w holdoucie tylko po parze gospodarz–gosc i dacie
  (+/- jeden dzien), a wynik jest porownywany dopiero na koncu.
- Zero modyfikacji aliasow, gdy w holdoucie pojawia sie nowa nazwa.
- Pusta proba kontrolna jest bledem, a nie wynikiem 100%.
- Tylko sumy: dopasowane, zgodne/rozne wyniki, duplikaty, nowe nazwy,
  niedopasowane i rozbieznosci dat.

Wykonanie `.github/workflows/api_football_holdout.yml`:
PR i push uruchamiaja wyłącznie testy offline. Tylko **ręczny**
`workflow_dispatch` moze zuzyc do **4** zapytan `/fixtures` (po dwa
na kazda lige), po sprawdzeniu statusu konta i rezerwy 100 zapytan.

**Ograniczenia:** OpenFootball w tym badaniu to snapshots z commitow
15.10.2026, a więc uzyskane po obu badanych okresach. To jest badanie
tozsamosci nazw i zgodnosci archiwalnych wynikow, NIE backtest
przedmeczowego modelu bez przecieku informacji z przyszlosci.
Nawet pelna zgodnosc nie dowodzi niezaleznie prawdziwosci wynikow ani
praw do komercyjnej publikacji danych. To nie jest zatwierdzona mapa
klubow, ani publikacja nowych lig na stronie.

Brak zmian w `predictions.json`, LAB 2.1/2.2 i silniku RZOTKIEWKI.

## Potwierdzony wynik — 11 listopada 2026, 17:14 UTC

[GitHub Actions — oddzielny wrzesniowy holdout](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43066246884)

Porownanie dwoch okien dla sezonu 2026/27. Nazwy klubow z okresu
kontrolnego **nie byly uzywane do wyznaczania aliasow**.

| Wskaznik | Premier League | LaLiga | Razem |
|---|---:|---:|---:|
| Mecze w zrodlach w oknie treningowym 21–31.08 (na zrodlo) | 20 | 23 | 43 |
| Kandydaci aliasow TYLKO z treningu | 6 | 11 | 17 |
| Mecze w okresie kontrolnym 4–14.09 (na zrodlo) | 20 | 20 | 40 |
| Dopasowane bez kandydatow aliasow w holdoucie | 11 | 3 | 14 |
| Dopasowane z niezmienionymi kandydatami w holdoucie | 20 | 20 | 40 |
| Zgodne wyniki po dopasowaniu | 20 | 20 | 40 |
| Niezgodne wyniki po dopasowaniu | 0 | 0 | 0 |
| Przesuniecia dni meczow | 0 | 0 | 0 |
| Nierozpoznane nowe nazwy zrodla w holdoucie | 0 | 0 | 0 |

- Wszystkie **10/10 testow offline** zaliczone.
- Status PRO przed uruchomieniem: 15/7500 wykorzystanych zapytan.
  Jednorazowy audyt zuzyl maksymalnie 4 odczyty /fixtures z juz
  oplaconego pakietu (po 2 na lige).
- Po audycie usunieto jednorazowy wyzwalacz. Pozostawiono tylko
  bezpieczny workflow manualny i testy offline w `main`.
- Dane OpenFootball przypieto do snapshotow z 15.10.2026; nie dowodzi
  to, ze mapa aliasow i wyniki byly znane na dzien meczow.
- Wynik **40/40** dowodzi tylko zgodnosci dwoch porownanych
  archiwalnych zrodel na odrebnym okresie. Nie dowodzi skutecznosci
  prognoz, niezaleznosci wszystkich dostawcow danych ani praw do publikacji.
- Wciaz potrzeba recznego, zewnetrznego potwierdzenia tozsamosci
  17 kandydatow, danych identyfikatorow druzyn oraz bezpiecznego,
  bezprzeciekowego backtestu przed jakimkolwiek wdrozeniem produkcyjnym.
- Brak zmian w `predictions.json`, `lab_forward/`, modelach i stronie.

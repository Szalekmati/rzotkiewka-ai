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

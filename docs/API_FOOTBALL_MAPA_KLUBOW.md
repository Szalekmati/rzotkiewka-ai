# RZOTKIEWKA AI – mapa tozsamosci klubow: etap propozycji (nie zatwierdzony)

Po audycie 30 niedopasowanych meczow potrzeba mapowania klubow
OpenFootball ↔ API-FOOTBALL. Nie wolno laczyc ich na podstawie zgodnosci
wyniku, punktow, kursow ani arbitralnego podobienstwa nazw.

Ten modul proponuje **wyłącznie niezweryfikowane kandydatury**:
- Dwa kraje/liga odseparowane; źródła z przypietych archiwów
  OpenFootball Premier League i LaLiga (2026/27).
- Normalizuje zapis imion klubow (akcenty, znaki, prefiksy FC/CF).
- Niektóre ogólne slowa są pomijane przy wyszukiwaniu potencjalnych
  duplikatów (de, club, rc, futbol, balompie). To NIE jest dowod.
- Wymaga zawarcia wszystkich istotnych slow jednej nazwy w drugiej i
  unikatowego, charakterystycznego slowa w obu zestawach ligowych.
- Kandydat jest jedynie proponowany, gdy relacja jest jednoznaczna 1:1.
- Porownuje liczbę par i rozbieżności **testowo** przy uzyciu kandydatów.
  Nie zapisuje ani nie publikuje proponowanych nazw/API rekordów.
- Istniejące, dokladne dopasowania pozostają bez zmian.
- W repozytorium nie powstaje produkcyjna mapa aliasow ani dane zespolow.

Workflow `api_football_alias_candidates.yml`:
PR/push = wyłącznie testy offline, bez API.
Wywołanie manualne = odczyt /status + **dwa** odczyty /fixtures,
z zachowaniem rezerwy 100 zapytań i tylko sumarycznym logiem.
W projekcie nie dotykamy prognoz `predictions.json`,
zamrozonego LAB 2.1/2.2 i strony.

**Następny etap:** potwierdzenie tozsamosci klubow i dopasowania ID na
zweryfikowanych niezaleznych źródłach, a dopiero potem jawna mapa aliasów
(z wersją, dowodami, testami regresji, bez zgadywania).

Dokumentacja API-FOOTBALL: https://www.api-football.com/documentation-v3

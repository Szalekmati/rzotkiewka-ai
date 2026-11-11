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

## Audyt kandydatow z 11.11.2026 (17:08 UTC)

[GitHub Actions — jednorazowy audyt 17 kandydatow](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43065131220)

Zakres: Premier League i LaLiga, 21–31.08.2026; jednoznaczne
proponowane mapowania nazw wyłącznie na podstawie struktury wyrazow,
bez uzycia wynikow meczow do doboru aliasu.

| Wskaznik | Premier League | LaLiga | Razem |
|---|---:|---:|---:|
| Wspolne nazwy klubow przed diagnoza | 14 z 20 | 9 z 20 | 23 |
| Nowe unikatowe kandydatury aliasow | 6 | 11 | 17 |
| Dopasowane mecze PRZED propozycjami | 9 z 20 | 4 z 23 | 13 z 43 |
| Dopasowane mecze PO zastosowaniu kandydatow badawczo | 20 z 20 | 23 z 23 | 43 z 43 |
| Zgodne koncowe wyniki w sparowanych meczach | 20 | 23 | 43 |
| Rozbieznosci koncowych wynikow | 0 | 0 | 0 |
| Zmiany dni meczow | 0 | 0 | 0 |
| Pozostale niedopasowane mecze w probie | 0 | 0 | 0 |

Testy offline: 10/10. Odczytano /status oraz 2 zapytania /fixtures
w ramach juz oplaconego planu PRO. Przed audytem licznik wykazywal 13
wykorzystanych zapytan z dziennego limitu 7500.

**Nie oznacza to 43 niezaleznie zweryfikowanych tozsamosci klubow.**
Zgodnosc w probie sugeruje, ze propozycje sa obiecujace, ale nie
dowodzi bezblednego mapowania we wszystkich rozgrywkach i sezonach.
Brak danych listopadowych w starym snapshotcie OpenFootball.
Proponowane aliasy nie sa zapisywane, automatycznie zatwierdzane ani
wykorzystywane w prognozach.

Nastepny etap: wersjonowana, jawna tabela mapowan zweryfikowana
niezaleznymi zrodlami klubow i datami kontroli; testy regresyjne
unikalnosci identyfikatorow oraz walidacja calego sezonu bez przecieku
danych przyszlych przy backtestach.

Po wykonaniu audytu usunieto jednorazowy wyzwalacz; pozostaje tylko
workflow reczny `api_football_alias_candidates.yml`.
`predictions.json`, LAB 2.1/2.2, strona i silnik produkcyjny pozostaly
niezmienione.

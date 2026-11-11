# RZOTKIEWKA AI — kiedy wrócą mecze w oknie modelu?

Moduł `api_football_next_window.py` to **badawcze sprawdzanie
terminarza**, a nie automat typowania. Oblicza datę UTC i polską
(CET/CEST) otwarcia pierwszego przyszłego okna na podstawie
`kickoff - 8 dni`; koniec kwalifikacji to **ściśle wcześniej**
niż `kickoff - 2 godziny`. Jest to dokładnie okno
czasu produkcyjnego silnika 2.1, ale nie zmienia jego działania.

- Premier League (39) i LaLiga (140), sezon 2026/27.
- Sprawdza tylko mecze `NS/TBD` z przyszłym kickoffem. Odrzuca
  przełożone, rozpoczęte, anulowane i rozliczone spotkania.
- Zawsze rozróżnia okna **aktywne teraz** i te, które dopiero
  się otworzą. Zestawia datę najbliższego meczu, najbliższe
  przyszłe otwarcie, zamknięcie i kickoff badanego spotkania.
- W logach pokazuje daty i metryki, bez nazw klubów, wyników,
  pojedynczych ID i surowej odpowiedzi dostawcy.
- Uwzględnia zmianę czasu polskiego z CET na CEST (IANA
  `Europe/Warsaw`), bez ręcznego zgadywania przesunięć.
- Dwa `/fixtures?league&season` na uruchomienie plus kontrola
  `/status`; wymagane pozostawienie 100 żądań rezerwy.
- **Nie ma harmonogramu.** Na PR/push uruchamiają się wyłącznie
  testy offline. Dostęp do API jest możliwy tylko na żądanie.
- Informacja o otwarciu okna nie potwierdza dostępności danych
  w przyszłości, ważności terminarza, praw do publikacji ani
  skuteczności prognozy. Datę należy potwierdzić ponownie.
- Moduł nie tworzy i nie zapisuje prognoz, nie otwiera
  `club_identity_release_gate`, nie zmienia LAB 2.1/2.2,
  `forecast_engine.py`, `predictions.json` ani strony.

Poprzedni raport o pustym oknie z 11.11.2026:
[GitHub Actions](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43070986881).

## Potwierdzony audyt 11 listopada 2026, 17:50 UTC

[GitHub Actions — wyznaczenie następnych okien](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43071963484).
Dane pobrano z API-FOOTBALL PRO dla sezonu 2026/27. Stan przed audytem:
31 z 7500 wykorzystanych zapytan. Audyt wykonal 2 wywolania `/fixtures`
w istniejacym pakiecie, bez nowych uslug.

| Pole | LaLiga | Premier League |
|---|---|---|
| Najblizszy kickoff (PL) | 20.11.2026, 21:00 CET | 21.11.2026, 13:30 CET |
| Otwarcie najblizszego okna badawczego (PL) | **12.11.2026, 21:00 CET** | **13.11.2026, 13:30 CET** |
| Zamkniecie okna (PL, wylacznie) | 20.11.2026, 19:00 CET | 21.11.2026, 11:30 CET |
| Przyszle mecze w katalogu | 260 | 280 |
| Aktywne okna w momencie audytu | 0 | 0 |
| Prognozy zapisane w tym audycie | 0 | 0 |

- Wyniki testow offline: **14/14**, workflow **success**.
- Godziny wskazuja, KIEDY pojedynczy mecz spelnia czasowe warunki
  istniejacego modelu 2.1; nie sa dowodem poprawnosci danych
  ani gotowosci Premium.
- Terminarz moze zostac zmieniony. **Przed kolejna decyzja
  nalezy sprawdzic ponownie faktyczny stan i historie druzyn**,
  a nie zakladac, ze zaplanowana data jest nadal aktualna.
- Bramka `club_identity_release_gate.py` nadal blokuje
  produkcyjne uzycie niezatwierdzonych map klubow i nowych lig.
- Nie zmieniono LAB 2.1/2.2, `predictions.json`,
  `forecast_engine.py` ani publicznego serwisu.
- Jednorazowy workflow testowy usunieto po sukcesie. Pozostal
  tylko reczny, read-only `api_football_next_window.yml`.

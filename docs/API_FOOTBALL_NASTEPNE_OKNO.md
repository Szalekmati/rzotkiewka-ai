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

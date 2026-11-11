# RZOTKIEWKA – analiza niedopasowanych meczow, bez zgadywania

Pierwsze porownanie OpenFootball i API-FOOTBALL:
[GitHub Actions](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43060940735).
Wczesniej: 43 mecze na zrodlo, dopasowane 13, 13 zgodnych wynikow,
30 niedopasowanych w kazdym zrodle.

Nowy audyt sprawdza, **dlaczego algorytm nie potrafil polaczyc rekordow**,
a nie zaklada bledow dostawcy. Kategorie dla kazdego niezidentyfikowanego
rekordu sa rozlaczne i sumuja sie do calkowitej liczby rekordow:

- `pair_other_date`: dokladnie te same znormalizowane nazwy pary
  gospodarze–goscie pojawiaja sie w drugim zrodle, ale poza +/- 1 dniem.
- `both_names_exist`: oba identyfikatory nazw wystepuja w przeciwnym
  zrodle w tej samej roli (dom/wyjazd), lecz nie ma tej pary.
- `only_home_name` / `only_away_name`: tylko jedna nazwa pasuje.
- `neither_name`: brak tych znormalizowanych nazw w odpowiednich rolach.

To **tylko diagnostyka**. Brak nazwy nie potwierdza rozbieznosci wyniku
ani tego, czy to ten sam klub: mozliwe aliasy, inne sklady lig, zmiany
terminow, ograniczenia zbioru historycznego. Nie dopasowujemy klubow na
podstawie podobienstwa wyniku (w ten sposob mozna zawyzyc zgodnosc).

Program nie loguje indywidualnych meczow ani nazw z prywatnej odpowiedzi
API i nie zapisuje danych dostawcy. Ręczne uruchomienie = co najwyzej
2 zapytania `/fixtures` w ramach juz oplaconego planu (proba z sierpnia
2026). PR/push uruchamiaja tylko testy offline. Bez zmian `predictions.json`,
`lab_forward/`, modelu i publicznej strony.

Nastepny krok po raporcie: zaplanowanie recznej weryfikacji konkretnych
aliasow i niezaleznej kontrolnej probki z zaufanego aktualnego zrodla,
bez automatycznego zatwierdzania meczow.

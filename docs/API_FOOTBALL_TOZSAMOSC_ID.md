# RZOTKIEWKA AI — kontrola identyfikatorow klubow w API-FOOTBALL

**Cel:** sprawdzic, czy identyfikatory zespolow pojawiajace sie w
terminarzach rzeczywiscie istnieja w oficjalnym katalogu /teams danego
sezonu i ligi. Nie jest to niezalezny dowod tozsamosci klubu
w dwóch odrebnych serwisach.

## Metoda
- Premier League ID 39 oraz LaLiga ID 140, sezon 2026.
- Okna: sierpien 21–31 (przygotowanie kandydatow) oraz wrzesien 4–14
  (kontrola nieskorygowanych aliasow).
- Dla kazdej ligi jedna odpowiedz `/teams?league=X&season=2026`
  i po dwie odpowiedzi `/fixtures`, razem maks. **6 wywolan** z limitu.
- Weryfikacja unikatowego dodatniego identyfikatora w /teams, czy
  identyfikatory rywali z /fixtures sa w katalogu, porownanie
  znormalizowanych nazw klubow oraz powtarzalnosci ID w 2 oknach.
- Brakujace identyfikatory lub warianty nazw maja status
  `DO_WERYFIKACJI_ID` lub `DO_WERYFIKACJI_NAZW`, nie sa przemilczane.
- Kandydaci nazw OpenFootball przypisani do unikatowych API team ID
  sa nadal **niezatwierdzeni** i nie trafiaja do produkcji. Do ich
  ostatecznego potwierdzenia potrzebne jest zewnetrzne, wiarygodne
  zrodlo identyfikacji klubow.
- Wyniki tylko jako liczniki w GitHub Actions. Skrypt nie loguje nazw
  klubow, danych meczowych, ID indywidualnych, adresow ani klucza.
- PR/push = wyłącznie testy offline. API tylko przez manualne uruchomienie.
- W planie zostaje 100 zapytan rezerwy, wykorzystanie max 6 wywolan
  dla kompletnego testu. Brak automatycznego harmonogramu.
- Nie dotyka `predictions.json`, `lab_forward/`, strony,
  modeli, eksperymentu LAB 2.1/2.2 ani wdrozeniowych aliasow.

Oficjalna dokumentacja: https://www.api-football.com/documentation-v3
Wg dostawcy ID druzyn sa unikatowe, a endpoint /teams przyjmuje
parametry league i season.

Badanie nie jest testem skutecznosci prognostycznej, ani sprawdzeniem
praw do komercyjnej publikacji danych.

## Potwierdzony audyt — 11 listopada 2026, 17:20 UTC

[Wyniki GitHub Actions #43067163631](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43067163631).

Weryfikacja team ID API-FOOTBALL na dwóch odrębnych oknach:
21–31.08.2026 oraz 4–14.09.2026, sezon 2026/27.
Nie zmieniano propozycji aliasów według danych holdoutu.

| Metryka | Premier League | LaLiga |
|---|---:|---:|
| Kluby w katalogu `/teams` | 20 | 20 |
| Mecze w oknie sierpniowym | 20 | 23 |
| Mecze w oknie wrześniowym | 20 | 20 |
| Unikatowe ID klubów w sierpniu | 20 | 20 |
| Unikatowe ID klubów we wrześniu | 20 | 20 |
| ID klubów wspólne dla obu okien | 20 | 20 |
| Wystąpienia nieznanych ID w meczach | 0 | 0 |
| Wariacje nazw wewnątrz API | 0 | 0 |
| Kandydaci aliasów z sierpnia | 6 | 11 |
| Kandydaci z unikatowym ID w katalogu API | 6 | 11 |
| Aliasów zatwierdzonych do produkcji | 0 | 0 |

- Testy offline: **14/14** zaliczone.
- Status konta PRO: przed odczytem **19/7500** dziennych zapytań.
  Audyt wykonuje maksymalnie sześć odczytów `/teams` i `/fixtures`
  razem (po 3 na ligę), bez dodatkowego zakupu.
- Wszystkie zbadane ID ze spotkań występują w katalogu odpowiedniej ligi
  i sezonu, a nazwy przypisane do tych ID są wewnętrznie spójne.
- **To nie jest niezależne potwierdzenie tożsamości aliasów między
  OpenFootball i API-FOOTBALL.** To test spójności **wewnątrz API**.
- Żadna mapa aliasów ani klubowe ID nie została zapisana jako
  produkcyjny słownik, nie użyto ich do prognoz.
- Wciąż potrzebne jest zewnętrzne potwierdzenie tożsamości 17
  kandydatów, najlepiej według oficjalnych stron lig/klubów, zanim
  powstanie wersjonowana mapa zatwierdzonych tożsamości.
- Usunięto jednorazowy wyzwalacz; do dyspozycji zostaje wyłącznie
  workflow uruchamiany ręcznie, z testami offline.
- Nie modyfikowano LAB 2.1/2.2, `predictions.json`, modeli ani strony.

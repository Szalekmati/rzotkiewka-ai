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

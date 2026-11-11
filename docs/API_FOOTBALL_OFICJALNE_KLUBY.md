# RZOTKIEWKA AI - niezalezne listy klubow 2026/27

Ten etap jest badaniem tozsamosci nazw w dwoch rozgrywkach.
Weryfikujemy 17 **kandydatow** pochodzacych z August 2026 OpenFootball
i API-FOOTBALL. Nie tworzymy automatycznie zatwierdzonego slownika ID.

## Niezalezne zrodla klubow

- [Oficjalna lista Premier League 2026/27](https://www.premierleague.com/en/news/4365156/premier-leagues-beginners-guide-all-you-need-to-know).
- [Oficjalna lista klubow LaLiga EA SPORTS 2026/27](https://www.laliga.com/en-US/laliga-easports/clubs).

Listy 20+20 klubow zostaly jawnie przepisane z tych witryn do
`api_football_official_roster.py` i opatrzone data kontroli
**11.11.2026**. To wersjonowana badawcza kopia listy nazw, a nie
automatycznie aktualizowany, licencjonowany feed danych.

## Kontrola

- Pobrac historyczny plik OpenFootball 2026/27 z przypietego commita
  (nie zapisujemy w repo rekordu meczowego);
- porownac nazwy klubow pojawiajace sie w sierpniu 2026;
- pobrac `/teams?league=39&season=2026` oraz `/teams?league=140&season=2026`;
  maksymalnie **2** odczyty z limitu planu PRO (plus `/status`);
- z trzecim niezaleznym oficjalnym spisem dopasowywac nazwy
  bez korzystania z bramek, kursow czy wynikow; wymagac rzadkiego
  rozpoznawalnego wyrazu, unikatowosci i zgodnosci zestawu wyrazow;
- osobno policzyc kandydatow wspartych trzecia lista, niejasnych,
  jawnie konfliktujacych i przypadki kolizji tozsamosci;
- drukowac tylko liczby, nigdy nazw/ID z odpowiedzi komercyjnego API.

**Nawet trójstronna zgodnosc nazwy NIE dowodzi, ze konkretne dwa
rejestry wskazuja na ten sam podmiot prawny, klub albo ID w każdym
meczu i sezonie.** Potrzebne jest dalsze sprawdzenie konkretnych
identyfikatorow klubow, pochodzenia danych i praw do publikacji.

Zadne mapowania nie sa zatwierdzane automatycznie.
Nie zmieniamy `predictions.json`, `lab_forward/`,
modelu ani strony. Testy `pull_request` i `push` sa bez dostepu
do API, a pobranie prawdziwych `/teams` jest tylko reczne.

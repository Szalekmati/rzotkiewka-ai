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

## Szczegolny przypadek: RC Deportivo

Oficjalny [profil ligowy klubu](https://www.laliga.com/es-GB/clubes/rc-deportivo)
pokazuje skrocona nazwe `RC Deportivo` i pelne okreslenie
`Real Club Deportivo de A Coruña SAD`.
Oficjalna [strona klubu — dane ogolne](https://www.rcdeportivo.es/es/datos-generales)
potwierdza pelne brzmienie z `A Coruña`. Klub
[opublikowal wyjasnienie zmiany pisowni nazwy](https://www.rcdeportivo.es/es/noticias/preguntas-y-respuestas-referentes-a-la-consulta-vinculante-sobre-la-denominacion-oficial-del-clu)
z `La Coruña` na `A Coruña`.

Przy analizie nazw wolno rozpoznac te DWA oficjalne pelne
warianty jako odniesienia do skrotu w oficjalnym spisie, ale tylko
w badaniu ligi 140. Nazwa samego `Deportivo` jest niejednoznaczna
(w lidze wystepuje rowniez Deportivo Alaves) i musi zostac odrzucona.

Ten dodatkowy dowod nie zatwierdza sam z siebie zadnego konkretnego
identyfikatora dostawcy ani automatycznej mapy aliasow w produkcji.

## Potwierdzone audyty z 11 listopada 2026

**Pierwszy odczyt:** [GitHub Actions #43068294486](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43068294486), 17:27 UTC.
Z oficjalnymi listami 2026/27 pasowalo 6 z 6 proponowanych aliasow
Premier League i 10 z 11 aliasow LaLiga (razem 16/17).
Pozostal jeden przypadek nierozpoznany, bez wykrytych konfliktow nazw.

**Rozszerzenie dowodow:** oficjalny
[profil RC Deportivo w LaLiga](https://www.laliga.com/es-GB/clubes/rc-deportivo),
[oficjalne dane klubu](https://www.rcdeportivo.es/es/datos-generales)
oraz [wyjasnienie nazwy La Coruña/A Coruña z maja 2026](https://www.rcdeportivo.es/es/noticias/preguntas-y-respuestas-referentes-a-la-consulta-vinculante-sobre-la-denominacion-oficial-del-clu).
Wprowadzono badawcze, jawne pelne formy nazwy `Real Club Deportivo
de A Coruña` i `Real Club Deportivo de La Coruña`, bez dopuszczenia
ogolnego `Deportivo` (istnieje tez Deportivo Alaves).

**Drugi odczyt:** [GitHub Actions #43068933528](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43068933528), 17:31 UTC.
Po uwzglednieniu oficjalnego nazewnictwa klubu:

| Metryka | Premier League | LaLiga | Razem |
|---|---:|---:|---:|
| Kluby w oficjalnych wykazach 2026/27 | 20 | 20 | 40 |
| Nazwy klubow OpenFootball rozpoznane wzgledem wykazu | 20 | 20 | 40 |
| Nazwy klubow API rozpoznane wzgledem wykazu | 20 | 20 | 40 |
| Kandydaci aliasow nazw | 6 | 11 | 17 |
| Kandydaci wspierani oficjalna lista nazw | 6 | 11 | **17** |
| Kandydaci nadal nierozpoznani w badaniu nazw | 0 | 0 | 0 |
| Konflikty i kolizje nazw z wykazem | 0 | 0 | 0 |
| Aliasow automatycznie zatwierdzonych do produkcji | 0 | 0 | **0** |

- Testy offline po poprawce: **16/16** zaliczone.
- Przeprowadzono dwa ograniczone audyty po maksymalnie dwa wywolania
  `/teams`, razem **4 zapytania** z istniejącego pakietu PRO
  (odczyt `/status` wykonany osobno).
  Przed pierwszym testem licznik wskazywal 25/7500, przed drugim 27/7500.
- **17/17 oznacza trójstronną zgodnosc nazw w badanym spisie**,
  NIE niezalezny dowod, ze identyfikatory klubow API mozna bezpiecznie
  laczyc z kazdym rekordem OpenFootball, ani ze model prognozuje trafnie.
- Same identyfikatory i kompletne listy komercyjnego API nie zostaly
  zapisane do repozytorium lub opublikowane.
- Przygotowano tylko wersjonowane referencje do nazw i zrodel,
  bez produkcyjnej mapy do prognoz.
- Oba jednorazowe wyzwalacze usunieto. Pozostaje reczny workflow
  `api_football_official_roster.yml` i offline testy.
- Historia prognoz, `predictions.json`, LAB 2.1/2.2, modele oraz
  publiczna strona pozostaly niezmienione.
- Przed wykorzystaniem premium potrzebne sa dalsze kontrole:
  konkretne identyfikatory w niezaleznym rejestrze, pelna historia,
  warunki licencyjne i prospektywny test predykcyjny.

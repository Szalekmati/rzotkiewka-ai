# RZOTKIEWKA AI — rejestr 23 rozbieżności UCL 2026/27

**Status: STOP / dokument badawczy. Bez automatycznych aliasów, poprawek wyników, wdrożenia terminarza, prognoz lub Premium.**

## Pochodzenie dowodu

- OpenLigaDB `ucl/2026`, rzeczywisty odczyt z **15 listopada 2026, 19:24 UTC**, [GitHub Actions #43752242775](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43752242775), [raport JSON](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43752242775/artifacts/14176364474).
- Referencja: [UEFA — oficjalny terminarz UCL 2026/27](https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-uefa-champions-league-all-the-league-phase-fixtures-a/), datowany 4 listopada 2026. Wewnętrzny limit przeglądu 7 dni został przekroczony (wiek 11 dni). **Data publikacji UEFA nie jest dowodem braku późniejszych korekt**.
- **49/72** par i godzin dopasowanych jednoznacznie, **23/72** niedopasowanych; 144 rekordy źródła, 72 mecze przyszłe. Metadane i struktura źródła przeszły sprawdzanie, lecz badawczy raport kończy się `STOP`.
- Poniższe parowanie wierszy to **hipotezy do ręcznej kontroli według godziny UTC, gospodarzy i gości**. Nie jest zatwierdzonym mapowaniem klubów ani ich identyfikatorów. Bez źródłowych `teamId` nie można poświadczyć tożsamości.

## Koncentracja problemów

| Etykieta występująca w OpenLigaDB | Liczba wystąpień w niedopasowanych parach | Ocena |
|---|---:|---|
| `FC Arsenal` | 4 | Kandydat do kontroli nazwy klubu Arsenal |
| `AS Rom` | 4 | Kandydat do kontroli nazwy klubu Roma |
| `Paris St. Germain` | 4 | Kandydat do kontroli nazwy Paris Saint-Germain |
| `FC Liverpool` | 4 | Kandydat do kontroli nazwy Liverpool |
| `Fenerbahçe SK` | 4 | Kandydat do kontroli nazwy Fenerbahçe |
| `Excelsior Rotterdam` | 4 | **KRYTYCZNY konflikt tożsamości z Barceloną** |

Pięć pierwszych etykiet dotyczy **19 unikalnych** niedopasowanych meczów,
ponieważ niektóre mecze łączą dwie takie nazwy. Ostatnie cztery
mecze zawierają `Excelsior Rotterdam` w miejscu, w którym
oficjalna referencja UEFA podaje **Barcelona**. Zgodność godziny
i rywala **nie uprawnia** do utożsamiania tych klubów.

## Rejestr wszystkich 23 niedopasowań

Wszystkie terminy w **UTC**. Podana para po stronie OpenLigaDB jest
kandydatem o tym samym czasie rozpoczęcia, nie automatycznie
zaakceptowanym odpowiednikiem oficjalnego spotkania.

| Kickoff UTC | UEFA: gospodarze – goście | OpenLigaDB: gospodarze – goście | Ocena |
|---|---|---|---|
| 2026-11-24 20:00Z | Arsenal – Borussia Dortmund | FC Arsenal – Borussia Dortmund | Nazwy do weryfikacji |
| 2026-11-25 17:45Z | Sabah – Barcelona | Sabah – Excelsior Rotterdam | **KRYTYCZNY: inny klub** |
| 2026-11-25 20:00Z | Club Brugge – Liverpool | FC Brügge – FC Liverpool | Nazwy do weryfikacji |
| 2026-11-25 20:00Z | Shakhtar Donetsk – Fenerbahçe | Shakhtar Donetsk – Fenerbahçe SK | Nazwy do weryfikacji |
| 2026-11-25 20:00Z | Paris Saint-Germain – Roma | Paris St. Germain – AS Rom | Nazwy do weryfikacji |
| 2026-12-08 20:00Z | Roma – Sporting CP | AS Rom – Sporting CP | Nazwy do weryfikacji |
| 2026-12-08 20:00Z | Aston Villa – Paris Saint-Germain | Aston Villa – Paris St. Germain | Nazwy do weryfikacji |
| 2026-12-08 20:00Z | Barcelona – Manchester City | Excelsior Rotterdam – Manchester City | **KRYTYCZNY: inny klub** |
| 2026-12-09 20:00Z | Arsenal – Real Madrid | FC Arsenal – Real Madrid | Nazwy do weryfikacji |
| 2026-12-09 20:00Z | LASK – Fenerbahçe | LASK – Fenerbahçe SK | Nazwy do weryfikacji |
| 2026-12-09 20:00Z | Liverpool – Porto | FC Liverpool – FC Porto | Nazwy do weryfikacji |
| 2027-01-19 20:00Z | AEK Athens – Roma | AEK Athen – AS Rom | Nazwy do weryfikacji |
| 2027-01-19 20:00Z | Inter – Liverpool | Inter Mailand – FC Liverpool | Nazwy do weryfikacji |
| 2027-01-20 17:45Z | Fenerbahçe – Villarreal | Fenerbahçe SK – Villarreal CF | Nazwy do weryfikacji |
| 2027-01-20 20:00Z | Como – Paris Saint-Germain | Como 1907 – Paris St. Germain | Nazwy do weryfikacji |
| 2027-01-20 20:00Z | Real Betis – Arsenal | Real Betis – FC Arsenal | Nazwy do weryfikacji |
| 2027-01-20 20:00Z | Sporting CP – Barcelona | Sporting CP – Excelsior Rotterdam | **KRYTYCZNY: inny klub** |
| 2027-01-27 20:00Z | Arsenal – Sabah | FC Arsenal – Sabah | Nazwy do weryfikacji |
| 2027-01-27 20:00Z | Roma – Lille | AS Rom – Lille OSC | Nazwy do weryfikacji |
| 2027-01-27 20:00Z | Atlético de Madrid – Fenerbahçe | Atletico Madrid – Fenerbahçe SK | Nazwy do weryfikacji |
| 2027-01-27 20:00Z | Barcelona – Como | Excelsior Rotterdam – Como 1907 | **KRYTYCZNY: inny klub** |
| 2027-01-27 20:00Z | Liverpool – Lens | FC Liverpool – RC Lens | Nazwy do weryfikacji |
| 2027-01-27 20:00Z | Paris Saint-Germain – Galatasaray | Paris St. Germain – Galatasaray Istanbul | Nazwy do weryfikacji |

## Przed odblokowaniem jakiegokolwiek spotkania

1. Sprawdzić aktualne dane u UEFA, w tym zmiany od 4 listopada.
2. Pobrać identyfikatory i surowe nazwy drużyn ze źródła do
   ograniczonego raportu diagnostycznego (bez kluczy i pełnej bazy),
   zweryfikować spójność tych samych `teamId` w sezonie.
3. Dla pięciu nazw-kandydatów potwierdzić klub w drugim źródle,
   udokumentować `teamId`, zakres i datę akceptacji przed ewentualnym
   **osobnym** PR dodającym jawne aliasy.
4. `Excelsior Rotterdam` **nie może** stać się aliasem Barcelony.
   Zgłosić niespójność dostawcy i sprawdzić przyczynę podmiany
   nazw/identyfikatorów.
5. Ponownie wykonać pełne porównanie 72 par i godzin na świeżych
   danych, a niezależnie zamknąć ocenę licencji i praw.

Wersja badawcza pozostaje oddzielona od `main`, `index.html`,
LAB 2.1/2.2, prognoz i Premium. Żadnych kosztów dodatkowych.

## Ustalenie identyfikatora źródłowego — 15.11.2026, 19:37 UTC

**Jednorazowy odczyt OpenLigaDB, tylko do badań:** [GitHub Actions #43753477790](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43753477790), krok `UCL - zbadaj jawne identyfikatory Excelsioru i Barcelony`. Zwrócono 144 mecze UCL 2026/27.

- `Excelsior Rotterdam` występuje **8 razy** i we wszystkich tych wierszach ma **`teamId: 356`**.
- W źródłowym sezonie nie występują etykiety `Barcelona` ani `FC Barcelona`: **0** rekordów z tymi nazwami.
- Wśród ośmiu meczów Excelsioru są **4 przyszłe**, które datowana referencja UEFA przypisuje Barcelonie. **4 wcześniejsze** spotkania z Excelsiorem (9.09, 13.10, 20.10 i 3.11) wymagają **osobnej** weryfikacji u UEFA; nie stwierdzamy ich zgodności na podstawie samego ID.
- Nie ma podstaw do uznania `356` za poprawny identyfikator Barcelony. To **spójna wewnętrznie, ale nieweryfikowana wobec UEFA identyfikacja dostawcy**. Brak dowodu, czy przyczyną jest błędna obsada ligi, powiązanie klubu, czy źródłowa zmiana danych.

**Decyzja:** `STOP`; nie tworzyć aliasu Excelsior–Barcelona i nie poprawiać `teamId` ręcznie. Zweryfikować źródłowy identyfikator Barcelony oraz listę uczestników 2026/27 niezależnie, przed ponownym porównaniem 72 meczów.

W repo pozostaje tylko odczytowy moduł `research/ucl_team_identity_probe.cjs` i jego testy offline. Po zapisaniu dowodów usunięto tymczasowy krok sieciowy z workflow PR. Brak skutków dla strony, modeli i Premium.

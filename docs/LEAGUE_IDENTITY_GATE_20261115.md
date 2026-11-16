# RZOTKIEWKA AI — nowe ligi: bramka spójności tożsamości (15.11.2026)

**Stan: tylko badania, bez publikacji i nowych źródeł płatnych.**

## Dlaczego powstała kontrola

W realnym audycie `schedule` z 15.11.2026: [run #43722236393](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43722236393),
w rekordach opisywanych jako LaLiga (`la1/2026`) pojawiły się
m.in. `SC Cambuur – AFC Ajax` i `AZ Alkmaar – Excelsior Rotterdam`.
Wśród meczów są też brakujące wyniki. **To sygnał możliwego pomieszania
rozgrywek lub błędu danych — przyczyna nie jest jeszcze rozstrzygnięta.**

Dotychczasowy audyt widział:
- Premier League i LaLiga: brak historycznych danych w badanych skrótach OpenLigaDB;
- UCL: kompletne badane sezony historyczne 2024/25 i 2025/26 (po 189 wyników),
  sezon 2026/27 144 rekordy, 72 wyniki i 72 przyszłe mecze; wybrane
  8/8 kontroli 2024/25 było zgodne z UEFA, bez pełnej weryfikacji 189 spotkań.

## Co robi nowa bramka

`tools/candidate_fixture_identity_gate.py` bierze **istniejący lokalny plik JSON**,
bez API i bez klucza, i weryfikuje:
- czy badana kandydatura ma przepisany wcześniej oficjalny wykaz 20 klubów na 2026/27
  (aktualnie ID 39 Premier League, ID 140 LaLiga);
- czy każde spotkanie ma poprawne ID, dwie różne drużyny i jawny czas UTC;
- czy czas rozpoczęcia należy do konserwatywnego okna sezonu 2026/27
  (od 1.07.2026 włącznie do 1.07.2027 wyłącznie); mecze spoza
  okna są blokowane do odrębnej, ręcznej weryfikacji;
- czy wszystkie nazwy klubów odpowiadają dokładnie (po normalizacji)
  nazwom z wykazu oraz czy nie ma sprzecznych mapowań nazwa ↔ ID;
- czy ta sama para gospodarze–goście nie występuje ponownie w sezonie
  pod innym ID lub terminem (w tych ligach rozgrywa się jeden mecz danej
  pary w tej kolejności; mecz rewanżowy z odwróconymi gospodarzami jest dozwolony);
- czy brak danych, duplikaty lub obce kluby powodują stan `BLOCKED`.

Przykładowa kontrola **lokalnie**, gdy mamy uprzednio pozyskany plik:
```sh
python tools/candidate_fixture_identity_gate.py --input /sciezka/do/laliga_2026.json --league-id 140 --season 2026
python -m unittest discover -s tests -p 'test_candidate_fixture_identity_gate.py' -v
```

Nie znamy poprawnych mapowań każdego ID dostawcy na klub, dlatego nawet
`NAMES_CONSISTENT_NEEDS_INDEPENDENT_REVIEW` **nie** pozwala uruchomić
kalendarza, prognoz ani subskrypcji. Odmienna pisownia prawdziwego klubu
też może zablokować kontrolę; aliasy należy weryfikować i dokumentować ręcznie,
a nie dopuszczać przez fuzzy match.

## Kolejność przed dołączeniem do strony

1. Zweryfikować dane i identyfikatory Premier League / LaLigi z drugim źródłem.
2. Przygotować osobny, aktualny roster UCL i niezależną kontrolę czasu, par,
   faz rozgrywek, wyników i korekt; UCL **nie jest** obsługiwany tą
   20-klubową bramką.
3. Dopiero po zaliczeniu bramek danych: przetestować nowy terminarz
   w kopii strony, bez prognoz i bez zmian LAB.
4. Po osobnej walidacji modelu rozważyć prognozy 1X2 i kontrolowany release.

**Nie zmieniać** `index.html`, `predictions.json`, `tips.json`,
`lab_forward/`, DNS, Pages, okresowych skanów ani żadnych usług płatnych
w ramach tego eksperymentu. Wynik CI `success` potwierdza testy kodu,
nie stanowi weryfikacji sportowej danych.
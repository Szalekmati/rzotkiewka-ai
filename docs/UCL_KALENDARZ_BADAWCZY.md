# RZOTKIEWKA AI — Liga Mistrzów: odizolowany terminarz testowy

**Etap:** research / draft. **Nie jest** częścią produkcyjnej strony i nie może zostać uznany za prawdziwe typy.

## Co przygotowano

- `research/ucl_calendar_preview.html` — samodzielny ekran do **ręcznego otwarcia** na Macu. Zachowuje rozpoznawalne ciemnozielone barwy i oryginalny znak 🫜, ale nie zmienia `index.html`.
- `research/ucl_calendar_preview.js` — odczyt i walidacja strukturalna terminarza **OpenLigaDB `ucl/2026`**; osobny, testowalny moduł, bez modelu 1X2.
- `tests/test_ucl_calendar_preview.cjs` — testy offline, m.in. duplikaty, błędne terminy, sprzeczne ID/nazwy zespołów, przeterminowane wyniki, przyszłe wyniki i brak danych.

**Dane nie są w repozytorium kopiowane ani publikowane.** Wyłącznie po kliknięciu `Pobierz terminarz badawczy` przeglądarka wykonuje bezpłatne, publiczne zapytanie GET do OpenLigaDB. W razie błędu albo niespójności nie pokazuje żadnych spotkań. Gdy bramka jakości strukturalnej przejdzie, wyświetla daty według `Europe/Warsaw`, fazę z odpowiedzi źródła, nazwy klubów i identyfikatory — nadal z ostrzeżeniem o braku niezależnej weryfikacji.

## Jak sprawdzić na MacBooku (tylko po pobraniu tej gałęzi)

1. Pobierz lub sklonuj gałąź `research/ucl-calendar-review-20261115`.
2. Otwórz `research/ucl_calendar_preview.html` w przeglądarce, zachowując znajdujący się obok `ucl_calendar_preview.js`.
3. Kliknij `Pobierz terminarz badawczy`; nie włączaj żadnych usług płatnych. Jeżeli Safari zablokuje odczyt przez CORS przy `file://`, możesz uruchomić lokalnie z katalogu repozytorium `python3 -m http.server 8000 --bind 127.0.0.1` i otworzyć `http://localhost:8000/research/ucl_calendar_preview.html`. To lokalny podgląd, nie publiczny serwer; zakończ `Control-C`.

**Uwaga:** dostępność API z danej przeglądarki nie jest jeszcze potwierdzona. Jeżeli odczyt się nie powiedzie, strona zgłosi STOP; nie używaj plików z fikcyjnymi wynikami jako zamiennika.

Testy offline: `node --test tests/test_ucl_calendar_preview.cjs`.

## Niezależna kontrola piątej kolejki (nowy etap)

W `research/ucl_official_matchday5.js` znajduje się datowane porównanie **18 par gospodarze–goście oraz godzin UTC** z oficjalnym [terminarzem UEFA 2026/27, opublikowanym 4.11.2026](https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-uefa-champions-league-all-the-league-phase-fixtures-a/). Pary te dotyczą wyłącznie piątej kolejki 24–25 listopada 2026. Istnieją ograniczone aliasy nazw klubów dostawcy, które są propozycjami roboczymi, nie zatwierdzonym powiązaniem ID.

**Warunek wyświetlenia kalendarza:** 18/18 jednoznacznych zgodności dat, godzin i kolejności gospodarze/goście oraz pozytywna kontrola strukturalna całego pobranego zestawu. Jedna niezgodność = STOP i brak wyświetlania. Nie potwierdzamy w ten sposób innych kolejek, identyfikatorów klubów, pełnej aktualności terminarza ani licencji.

Testy offline: `node --test tests/test_ucl_calendar_preview.cjs tests/test_ucl_official_matchday5.cjs`. Testy nie pobierają danych i nie dowodzą rzeczywistej zgodności OpenLigaDB z UEFA. Zmiany terminów na stronie UEFA po 4.11 wymagają ręcznej aktualizacji referencji i sprawdzenia.

## Rozszerzenie: 72 spotkania kolejek 5–8

Dodatkowo przepisano z **tego samego, datowanego 4.11.2026 wykazu UEFA** wszystkie
72 pary i godziny meczów końcowych czterech kolejek fazy ligowej:
24–25 listopada (18), 8–9 grudnia (18), 19–20 stycznia (18) i 27 stycznia (18).
Dane odniesienia są w `research/ucl_official_matchday5.js`
(nazwa pliku jest historyczna: zapis kolejek 5–8).
Interfejs `research/ucl_calendar_preview.html` wymaga teraz zgodności
**72/72 par i terminów**; nawet jeden brak = brak pokazywanego terminarza.
Dodatkowa bramka blokuje także **każdy nadprogramowy mecz źródła po
4 listopada 2026**, którego pary gospodarzy/gości i godzin nie ma w tych
72 pozycjach. Samo 72/72 nie może już przepuścić nieznanej karty.
Dotyczy to również przyszłych faz pucharowych — podgląd fazy ligowej
musi wtedy zgłosić STOP aż do przygotowania nowej, oddzielnie zweryfikowanej
referencji; nie wolno automatycznie uznać tych meczów za potwierdzone.
Sprawdzenie nadal nie obejmuje pełnych wyników zakończonych meczów,
weryfikacji ID drużyn z UEFA, przesunięć terminów po dacie referencyjnej
ani praw do wykorzystania danych.

Testy offline obejmują rozkład 72 par, brak jednego meczu, zmianę godziny
i zamianę gospodarza/gościa w innym terminie. **Symulowane dane w testach
nie dowodzą, że prawdziwa odpowiedź OpenLigaDB przechodzi tę bramkę.**
Adres API nie był jeszcze skutecznie odczytany i porównany z tego środowiska.
Przed zatwierdzeniem potrzebny jest audyt rzeczywistego pobrania oraz
aktualnego terminarza UEFA.

## Warunki zanim Liga Mistrzów trafi na właściwą stronę

1. Potwierdzić pełen oficjalny spis drużyn UCL 2026/27, pary gospodarze/goście, fazy, terminy i ewentualne przesunięcia u UEFA.
2. Zweryfikować powiązanie identyfikatorów drużyn oraz wykrywać sprzeczne rekordy, nie tylko poprawną składnię.
3. Sprawdzić licencję i warunki komercyjnego wykorzystania terminarza, poprawność wyników historycznych i ich datowania.
4. Wprowadzić na stronę **najpierw terminarz oznaczony jako zweryfikowany**, a osobno później modele prognoz 1X2 po ich własnej walidacji.
5. Scalanie i publikacja wymagają osobnej kontroli. Żaden test ani przycisk w tym PR nie może aktywować prawdziwych prognoz ani Premium.

Ostatni referencyjny audyt repozytorium z **15.11.2026**: [GitHub Actions #43722236393](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43722236393), UCL 2026/27: 144 rekordy (72 zapisane wyniki, 72 przyszłe); status **DO RĘCZNEJ OCENY**. Ten wynik jest punktem odniesienia, a nie gwarancją identycznego wyniku przy kolejnym pobraniu.

**Nie zmieniono:** produkcyjnego `index.html`, `predictions.json`, `tips.json`, `lab_forward/`, harmonogramów LAB, ustawień Pages, domeny i integracji płatnych.

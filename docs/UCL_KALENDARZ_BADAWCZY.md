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

## Ręczne porównanie rzeczywistego snapshotu bez publikacji

Dodano `research/ucl_verify_snapshot.cjs` — samodzielny, odczytowy raport
wywoływany **wyłącznie na żądanie**, bez nowego harmonogramu i bez odpytywania
API w testach CI. Wymaga Node.js 18+.

- `node research/ucl_verify_snapshot.cjs --file /sciezka/do/istniejacego_snapshotu.json`
  — porównanie już istniejącego lokalnego JSON, bez internetu.
- `node research/ucl_verify_snapshot.cjs --live` — **jawny**, pojedynczy odczyt
  publicznego OpenLigaDB `/getmatchdata/ucl/2026`, timeout 14 s, limit 3 MB,
  bez zapisywania surowych danych do repozytorium i bez kluczy API.
- `node --test tests/test_ucl_verify_snapshot.cjs` — testy offline na danych
  syntetycznych, włączone do istniejącego CI audytu nowych lig.

Każdy rekord musi dodatkowo deklarować `leagueShortcut="ucl"` oraz
`leagueSeason=2026`. Brak takiego oznaczenia lub inna liga/sezon = `STOP`;
Wszystkie rekordy muszą ponadto mieć ten sam dodatni identyfikator
`leagueId` (liczba całkowita), zgodnie ze schematem OpenLigaDB.
Niejednolite lub brakujące `leagueId` oznacza `STOP`; sam wspólny
identyfikator od jednego dostawcy nie jest niezależnym dowodem tożsamości ligi.
Zgodna para drużyn i data nie zastępują kontroli pochodzenia rekordu.
Ta sama bramka obowiązuje też w przeglądarkowym podglądzie
`research/ucl_calendar_preview.html` (wspólny walidator
`UclPreview.sourceIdentityValid`); testy offline obejmują pola błędne,
puste i nieobecne. Schemat OpenLigaDB dopuszcza wartości null, dlatego
rzeczywiste dane bez jednoznacznego oznaczenia zostaną celowo
zatrzymane, bez zgadywania na podstawie adresu URL. Jest to kontrola
spójności metadanych, nie niezależne poświadczenie prawdziwości źródła.

W raporcie: `MATCHED_RESEARCH_ONLY` oznacza poprawność ograniczonego
porównania danych ze stanem datowanej referencji UEFA i kontrolami technicznymi,
**nigdy** zgodę na publikację lub prognozy. `STOP` albo błąd odczytu blokują
interpretację. Niezamknięta kontrola obowiązków licencji ODbL i brak niezależnej kontroli ID klubów
pozostają osobnymi bramkami. Żadne wykonanie narzędzia nie zmienia strony,
LAB, prognoz, cen ani płatności.

## Prototyp scentralizowanego cache — tylko lokalny, bez sieci

`research/ucl_central_snapshot.cjs` jest prototypem czystej transformacji
wcześniej pozyskanego pliku JSON w niewielki **snapshot badawczy**, oparty na
wspólnych bramkach `compareRows` i `UclPreview.inspect`. Nie odczytuje API,
nie zmienia publicznych danych i nie uruchamia harmonogramów.

```sh
node research/ucl_central_snapshot.cjs --input /tmp/ucl_2026.json --output /tmp/ucl_research_snapshot.json
```

Wynik powstaje wyłącznie po zgodności źródła z datowaną referencją UEFA
(72 pozycji) i kontrolą struktury. Nie nadpisuje pliku wyjściowego. Zawiera
jedynie wymagane pola meczów bez grafik, URL herbów i surowych wyników.
Ma jawne `observed_at_utc`, pochodzenie, licencję ODbL, oraz limit świeżości
6 godzin. Funkcja `inspectResearchSnapshot` wykrywa wygasłe i przypadkowo
zmienione zestawy; SHA-256 kontroluje spójność, nie poświadcza źródła.
Każdy wynik ma **`RESEARCH_ONLY`** oraz trzy flagi zakazu publikacji,
prognoz i Premium. **Nie jest częścią `index.html` i nie może być automatycznie
udostępniany użytkownikom.**

Testy offline: `node --test tests/test_ucl_central_snapshot.cjs`, także
w ramach istniejącego audytu PR. Samo CI nie wykonuje odczytu API.
Do wdrożenia centralnego cache w przyszłości wymagane są osobne decyzje
dotyczące trybu odświeżania, limitu Actions, praw do danych i rollbacku.

## Licencja i fair use OpenLigaDB — przegląd 15.11.2026

Źródła: [OpenLigaDB — licencja danych](https://www.openligadb.de/en/license)
(aktualizacja wskazana przez dostawcę: 07.11.2026),
[OpenLigaDB — regulamin dostępu API](https://www.openligadb.de/en/terms-of-use).
Angielskie strony to tłumaczenia pomocnicze; według dostawcy wiążący tekst
jest po niemiecku. Niniejsza notatka nie jest formalną opinią prawną.

**Wniosek:** ODbL 1.0 dopuszcza wykorzystanie danych meczowych OpenLigaDB
**także w produktach płatnych**. Sama komercyjność naszej przyszłej aplikacji
nie jest zakazem. Nadal należy zapewnić przypisanie źródła i licencji.
Przykład widocznej informacji: `Dane: OpenLigaDB (ODbL 1.0)` z odnośnikiem
w stopce lub sekcji źródeł. Publiczne rozpowszechnianie zmodyfikowanej bazy
danych może uruchamiać obowiązki share-alike i zakaz nakładania ograniczeń
technicznych na dalej udostępnianą bazę. Sam widok tabeli w aplikacji dostawca
opisuje inaczej niż redystrybucję bazy; konkretny sposób publikacji i
przetwarzania danych trzeba jednak sprawdzić przed wdrożeniem.

Licencja **nie obejmuje** herbów, logo, obrazów pod odnośnikami API ani nie
znosi praw do nazw i znaków klubów. Treści UEFA i API-FOOTBALL wymagają
**oddzielnej** oceny praw; nie wolno przenosić na nie warunków OpenLigaDB.

**Fair use i architektura:** zalecany jest centralny cache, nie pobieranie
pełnego terminarza osobno przez każdy telefon. Według regulaminu:
- najpierw sprawdzać `getlastchangedate`, a pełne dane pobierać po zmianie;
- podczas meczów najwyżej raz na 30–60 sekund dla każdej ligi **łącznie**,
  poza meczami zwykle wystarcza kilka odczytów dziennie;
- stosować cache, jitter, wykładniczy backoff po HTTP 429/5xx i identyfikujący
  `User-Agent` z nazwą projektu i kontaktem;
- obsługiwać awarie, braki i opóźnienia bez wymyślania wyników lub terminów.

Obecny ręczny `ucl_calendar_preview.html` pozostaje **tylko lokalnym,
niepublikowanym narzędziem badawczym**. Jego bezpośredni odczyt API z
przeglądarki nie jest wzorcem na publiczne wdrożenie dla wielu osób.
Centralny cache z limitem świeżości, nadzorem kosztów i poprawną atrybucją
będzie wymagać osobnego projektu i zatwierdzenia; tej gałęzi nie wolno
scalać ani publikować automatycznie.

## Zabezpieczenie aktualności referencji UEFA (etap badawczy)

Raport `research/ucl_verify_snapshot.cjs` porównuje spotkania z datowanym
spisem UEFA z **4.11.2026**. Ponieważ terminarze mogą się zmieniać, dodano
**wewnętrzny, ostrożny limit ponownej weryfikacji: 7 pełnych dni UTC**
(nie jest to limit narzucony przez UEFA). Po upływie tego okresu lub przy
błędnym czasie raport daje `STOP`, nawet jeśli wszystkie 72 spotkania nadal
pasują do starej referencji. Do raportu trafiają
`referenceAgeDays`, `referenceReviewMaxDays` i
`referenceReviewRequired`. Z tego samego powodu nie wolno zbudować
badawczego cache na przestarzałym porównaniu.

Przykład: **15.11.2026 referencja ma 11 dni, więc wynik musi być STOP**
do ponownego udokumentowanego sprawdzenia oficjalnego wykazu u UEFA.
Odświeżenie oznacza rzeczywiste porównanie zmian i aktualizację daty
referencji wraz z testami, **nie** ręczne przestawienie daty w kodzie.
Nawet `MATCHED_RESEARCH_ONLY` w krótszym oknie nie dopuszcza
publikacji ani prognoz. Ten limit chroni również przed przypadkowym
użyciem historycznego raportu jako dowodu aktualności API.

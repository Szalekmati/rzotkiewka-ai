# RZOTKIEWKA AI — OpenLigaDB: prawa do danych, dostęp API i plan centralnego cache

**Stan przeglądu: 15.11.2026.** **Wydanie nowych lig: STOP.** Dokument badawczy bez wdrożenia, zmian Premium, LAB, DNS czy kosztów.

## Zweryfikowane dokumenty dostawcy

1. [Licencja danych OpenLigaDB (niemiecka, wersja wiążąca)](https://www.openligadb.de/lizenz), stan na 07.11.2026.
2. [Warunki dostępu do API OpenLigaDB](https://www.openligadb.de/nutzungsbedingungen), stan na 07.11.2026.
3. [ODbL 1.0 — pełny tekst](https://opendatacommons.org/licenses/odbl/1-0/).
4. [API / Swagger](https://api.openligadb.de/index.html) — schemat `Match`, w tym `leagueId`, `leagueShortcut`, `leagueSeason`.

**Wniosek wstępny, nie opinia prawna:** ODbL 1.0 zezwala na komercyjne używanie sportowych danych OpenLigaDB i tworzenie własnych analiz oraz prognoz przy dotrzymaniu warunków. Publiczne wykorzystanie danych wymaga atrybucji. Jeśli RZOTKIEWKA publicznie udostępni zmodyfikowaną bazę danych, trzeba osobno ocenić obowiązek udostępnienia tej bazy na ODbL (share-alike) oraz zakaz blokowania odbiorcom korzystania z praw do bazy. Samo wyświetlanie terminarza lub wykresów nie oznacza automatycznie, że wszystkie elementy aplikacji podlegają ODbL. To nie zastępuje oceny prawnej konkretnego sposobu dystrybucji.

**Osobne prawa:** herbów, znaków klubowych, logotypów i zewnętrznych grafik z `TeamIconUrl` nie obejmuje licencja danych OpenLigaDB. W badawczym kalendarzu używać tylko nazw, par i dat oraz oryginalnego znaku RZOTKIEWKI. Nie pobierać ani nie osadzać automatycznie cudzych herbów. Dane UEFA użyte do porównania terminarzy są źródłem kontroli faktów, ale nie stanowią zgody na kopiowanie chronionych materiałów UEFA do komercyjnego produktu.

## Stan kodu, odczyt z gałęzi main (15.11.2026)

`index.html` zawiera odwołania do `https://api.openligadb.de/getmatchdata/...` bezpośrednio z przeglądarki i z `cache:'no-store'`, m.in. okolice linii 1975 (terminarz), 2027 (trzy ligi) oraz 2720 (przedmeczowe okna danych). Na stronie jest już atrybucja OpenLigaDB/ODbL, także w stopce. Nie twierdzimy, że bieżąca liczba użytkowników narusza regulamin; ten wzorzec wymaga zmiany **przed** zwiększeniem ruchu, zakresu lig i uruchomieniem Premium.

Dostawca prosi o *jeden centralny odczyt* na całą aplikację i serwowanie użytkownikom danych z własnej pamięci podręcznej, zamiast osobnego pobrania dla każdej przeglądarki. Poza trwającymi meczami zwykle wystarcza kilka odczytów dziennie; podczas meczów co najwyżej jeden odczyt na ligę co 30–60 sekund. Preferuje `getlastchangedate` jako tanią kontrolę zmian. Zaleca losowe przesunięcie (jitter), backoff dla HTTP 429/5xx, wyraźny `User-Agent` z kontaktem i odporność na przerwy w działaniu. Nie ma gwarancji SLA ani redakcyjnej weryfikacji wyników. API jest aktualnie darmowe, ale warunki dostępu mogą się zmienić.

## Plan techniczny — nie uruchamiać automatycznie

1. **Faza A: katalog źródeł.** Jedna jawna lista `leagueShortcut` + `leagueSeason`, identyfikator ligi z dostawcy, metadane źródła i data ostatniej kontroli; żadnych dopasowań „na oko” ani niezatwierdzonych aliasów. Liga Mistrzów nadal `research only`.
2. **Faza B: odczyt scentralizowany.** Rozważyć istniejący harmonogram GitHub Actions jako źródło kilku dziennych, kontrolowanych aktualizacji dla podłączonych lig, bez nowej infrastruktury i bez dodatkowej częstotliwości; alternatywa serwerowa dopiero z osobną zgodą i oceną kosztów. Najpierw bezpieczny podgląd i sprawdzenie zużycia Actions.
3. **Faza C: walidacja.** Przed zapisaniem snapshotu sprawdzić pełen zestaw pól, UTC, sezon i ID drużyn, status zakończenia, niesprzeczne wyniki, brak duplikatów; nowe ligi dodatkowo kontrolować względem niezależnego źródła. Błąd = STOP; nie nadpisywać ostatniego zatwierdzonego snapshotu.
4. **Faza D: serwowanie.** Użytkownik pobiera raz opublikowany, podpisany czasem snapshot JSON z GitHub Pages, nie odpytuje osobno OpenLigaDB. Jawna metryka `observed_at_utc`, `source`, `quality_status`; starsze dane tylko z widoczną informacją „mogą być nieaktualne”, nigdy „LIVE”. Zdefiniować dopuszczalny wiek danych i czas awarii; brak snapshotu = komunikat zamiast wymyślonych spotkań.
5. **Faza E: pomiary i rollback.** Liczba odczytów, błędy HTTP, wiek snapshotu, kompletność, limity i ścieżka wycofania. Przed zmianą Pages/DNS/lab/pricing oddzielny przegląd, test mobilny oraz zgoda właściciela projektu.

**Uwaga kosztowa:** repo GitHub i istniejące Actions mogą posłużyć do prototypu, ale nie zakładamy bez sprawdzenia, że intensywniejsza automatyzacja jest darmowa przy dowolnym obciążeniu. Bez zgody użytkownika nie kupować niczego ani nie zwiększać harmonogramów.

## Bramka przed komercyjnym wydaniem

- [ ] Sprawdzono źródło i licencję wszystkich danych użytych w konkretnym ekranie (OpenLigaDB versus API-Football versus dane własne).
- [ ] Atrybucja jest widoczna na stronie oraz w ekranach korzystających z danych.
- [ ] Zewnętrzne herby, logotypy i grafiki nie są automatycznie pobierane bez praw.
- [ ] Rozstrzygnięto, czy eksport/udostępnianie zmodyfikowanej bazy uruchamia ODbL share-alike; opracowano zgodny sposób udostępnienia danych.
- [ ] Zastąpiono pobieranie danych per przeglądarka scentralizowanym, limitowanym cache dla oczekiwanego ruchu.
- [ ] API nie jest krytyczną zależnością w czasie renderowania strony; obsłużono 429/5xx, awarie, staleness i aktualizacje.
- [ ] Nowe ligi zaliczyły niezależną kontrolę klubu, ID, wyniku i terminarza.
- [ ] Model 1X2 przeszedł oddzielny forward test; funkcje Premium, strona i domena mają osobną zgodę na wdrożenie.

**Obecny stan:** dokumentuje ryzyka, niczego nie aktywuje. Żaden wynik nie dopuszcza automatycznie UCL, Premier League ani LaLigi do produkcyjnych prognoz.

# 🫜 RZOTKIEWKA — źródła danych, licencje i zasady API

Stan weryfikacji: **10 listopada 2026**. Dokument techniczno-produktowy, nie porada prawna.

## 1. OpenLigaDB — dane meczowe

**Źródło:** https://www.openligadb.de/

**Licencja:** [Open Database License (ODbL) 1.0](https://www.openligadb.de/lizenz).
OpenLigaDB potwierdza możliwość użycia danych także w produktach płatnych i komercyjnych.

Na stronie publicznej należy umieścić widoczny podpis, na przykład:
> Dane od OpenLigaDB (www.openligadb.de), licencja ODbL 1.0.

W aplikacji podpis jest w sekcji meczów i w stopce wszystkich ekranów.

**Ważne rozróżnienie:** samo wyświetlanie danych w tabelach/aplikacji co do zasady wymaga
atrybucji, ale publiczne rozpowszechnianie **zmodyfikowanej bazy danych** może uruchomić
obowiązek oferowania tej bazy na ODbL na tych samych warunkach. Należy osobno
przeanalizować politykę publikowanych plików danych, archiwum i dalszą redystrybucję.

Własne analizy i modele predykcyjne nie stają się automatycznie objęte ODbL
tylko dlatego, że używają tych danych (zgodnie z informacją licencjodawcy).
Nie oznacza to nabycia praw do danych lub znaków osób trzecich.

**Nie kopiować automatycznie herbów, logotypów i obrazów podanych w `TeamIconUrl`.**
Licencja ODbL danych ich nie obejmuje. Nazwy klubów i oznaczenia również mogą
podlegać prawom znaków towarowych.

Źródło zasad: https://www.openligadb.de/lizenz (stan: 07.11.2026).

## 2. Zasady uczciwego korzystania z API

Źródło: https://www.openligadb.de/nutzungsbedingungen (stan: 07.11.2026).

- Sprawdzać `getlastchangedate` przed kosztownym pobraniem pełnego terminarza,
  jeśli realizujemy częste odświeżanie.
- Podczas meczu: nie częściej niż co 30–60 sekund **na ligę łącznie**,
  nie na użytkownika ani urządzenie. Poza meczami zwykle kilka odczytów dziennie.
- Stosować pamięć podręczną, rozłożone w czasie zapytania, backoff dla HTTP 429 i 5xx.
- Dla większej liczby użytkowników: **jednorazowe centralne pobieranie**,
  serwowanie klientom danych z własnej pamięci podręcznej. Nie wolno bez
  ponownego przemyślenia tej architektury skalować strony z zapytaniami wprost
  z każdego telefonu.
- W serwerowych integracjach wysyłać czytelny `User-Agent` z nazwą aplikacji
  i opcjonalnie publicznym kanałem kontaktowym.
- OpenLigaDB jest bazą społecznościową; brak gwarantowanego SLA, błędy i
  opóźnienia są możliwe. Nie traktować wyników jako niezależnie zweryfikowanych.

Dokumentacja techniczna API: https://api.openligadb.de/ .
Opisuje również limit **60 żądań/minutę/IP**.

## 3. Uczciwy stan naszego projektu

Obecna aplikacja GitHub Pages wykonuje część odczytów bezpośrednio z przeglądarki.
To **wersja badawcza**, nie architektura produkcyjna dla dużej skali.

Przed szeroką promocją, masowym ruchem lub startem Premium:
1. Zbudować i przetestować centralny cache oraz odświeżanie po znaczniku zmiany,
   z obsługą 429/5xx i ograniczeniem liczby pobrań.
2. Dodać obserwowalność źródła: daty pobrań, wiek cache, błędy, opóźnione wyniki.
3. Potwierdzić poprawne przypisanie ligi i sezonu oraz licencje każdej dodatkowej bazy.
4. Zweryfikować reguły redystrybucji ODbL przy publikacji baz/zbiorów pochodnych.
5. Dla dużego wdrożenia skontaktować się z operatorem OpenLigaDB;
   dane kontaktowe są na stronie warunków.
6. Nie pobierać logotypów klubowych bez odrębnych uprawnień.

## 4. UEFA

Oficjalne wyniki UEFA służą w projekcie jako **punkty kontrolne do porównania
z danymi OpenLigaDB**, nie jako ogólne pozwolenie na pobieranie i redystrybucję
oficjalnej bazy UEFA, obrazów, logotypów czy brandingu.

Historyczny audyt `ucl_deep_audit.py` przeprowadza wybrane porównania
z https://www.uefa.com/uefachampionsleague/news/0290-1bbe6365b47a-0668db2bbcb1-1000/ .
Zgodność 8/8 wybranych spotkań **nie oznacza** sprawdzenia wszystkich 189 meczów.
Nowe ligi nie są dodawane automatycznie do silników lub LAB.

## 5. Zasada wdrożeń

Modele LAB 2.1/2.2, archiwum prognoz oraz metryki jakości są niezależne
od audytu licencji i nowych lig. Żaden raport wstępny nie oznacza automatycznej
zgody na produkcyjne prognozowanie czy pobieranie opłat.

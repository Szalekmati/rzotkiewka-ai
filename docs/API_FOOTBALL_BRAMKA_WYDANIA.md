# RZOTKIEWKA AI — bramka dopuszczenia nowych lig i nazw klubow

**Stan na 11.11.2026: BLOKADA PRODUKCJI NOWYCH LIG.**
To normalny i oczekiwany stan w trakcie badań. Istniejące wdrożenie
Bundesligi i zamrożony LAB 2.1/2.2 działają niezależnie od tej bramki.

## Co już potwierdziliśmy
- Siedem lig w katalogu API-FOOTBALL 2026 — badanie metadanych.
- 99 rekordów meczów z siedmiu lig — brak wykrytych błędów struktury
  w 10-dniowej próbie, **nie** potwierdzenie wszystkich wyników.
- 43 mecze sierpniowe + 40 wrześniowych spójne w parowanych wynikach
  OpenFootball/API-FOOTBALL po badawczym mapowaniu nazw.
- 17/17 propozycji aliasów wspartych przez oficjalne wykazy nazw
  Premier League (6) i LaLiga (11), w tym udokumentowane warianty
  nazwy RC Deportivo.
- Identyfikatory klubów są spójne **wewnątrz** API-FOOTBALL:
  17/17 kandydatów nazw można powiązać z unikatowym ID w katalogu API.

## Czego ten wynik NIE dowodzi
- **0/17** konkretnych powiązań OpenFootball ↔ provider team ID zostało
  ręcznie zatwierdzonych w niezależnym rejestrze klubu, z indywidualnym
  dowodem i osobą dokonującą weryfikacji.
- 0 dopuszczonych map identyfikatorów do produkcyjnego adaptera.
- Brak ostatecznej decyzji dotyczącej praw do publikacji danych API.
- Brak zatwierdzonego prospektywnego testu jakości prognoz dla
  nowych lig. Zgodność wyników historycznych to nie skuteczność typów.

## Kontrolowany rejestr

`data/identity_release_registry.json` przechowuje jedynie metryki
zagregowane, odnośniki do oficjalnych spisów i historii audytów oraz
pustą listę `reviewed_identity_links`. Nie publikuje surowych rekordów
API, identyfikatorów klubów ani prywatnych danych konta.

Aby w przyszłości stworzyć **zweryfikowany** wpis tożsamości klubu,
potrzeba m.in.: rozgrywek/sezonu, nazwy z publicznego źródła,
unikatowego team ID, niezależnego źródła identyfikacji konkretnego
klubu, daty i osoby dokonującej przeglądu. Zduplikowane identyfikatory
i przypadki bez niezależnych dowodów są odrzucane.

Status `rights_review_approved` wymaga podpisanego raportu o prawach
do wykorzystania danych. `forward_time_model_test_approved` wymaga
raportu z testu prognoz zapisanych przed meczem. Żadna flaga nie może
zostać uznana za poprawną tylko dlatego, że GitHub Actions jest zielony.

## Przed publikacją / Premium

Bramka kodowa w `club_identity_release_gate.py` jest domyślnie
**fail-closed**: nigdy nie oznacza mapowania jako automatycznie
dopuszczonego do produkcji. `python club_identity_release_gate.py`
sprawdza poprawność rejestru i wypisuje **PRODUKCJA NOWYCH LIG:
ZABLOKOWANA**, nawet kiedy testy offline są zielone.
Tryb `--require-release` kończy się niepowodzeniem i może zostać
użyty jako wymagany krok przyszłego pipeline'u wydania.

Nowe funkcje pozostają odłączone od `forecast_engine.py`,
`predictions.json`, `lab_forward/`, `index.html` i Premium.
Przed wydaniem potrzebna jest **osobna decyzja oraz sprawdzona
implementacja adaptera**. To ograniczenie jest celowe.

Źródła: [raport nazw 17/17](API_FOOTBALL_OFICJALNE_KLUBY.md),
[spójność ID](API_FOOTBALL_TOZSAMOSC_ID.md),
[holdout](API_FOOTBALL_HOLDOUT.md),
[zasady danych](DANE_I_LICENCJE.md).

Cały workflow `identity_release_gate.yml` działa **offline**.
Nie wykorzystuje klucza API-FOOTBALL i nie uruchamia płatnych usług.

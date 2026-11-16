# RZOTKIEWKA AI — API-Football, prawa do danych i plan Premium (16.11.2026)

**Status: RESEARCH_ONLY / RIGHTS_REVIEW_REQUIRED.** Materiał do przeglądu produktu i konsultacji prawnej, **nie** zgoda na publikację ani opinia prawna. Nie zakupiono usług, nie uruchomiono API ani nie zmieniono płatności.

## Źródła z datą kontroli

1. **API-Football / API-Sports — oficjalny regulamin usługi:** https://www.api-football.com/terms (odczyt 16.11.2026; strona wskazuje aktualizację 21.05.2025). Istotne sekcje: `Terms of use`, `Service & data`, `Data/Logos/images`.
2. **OpenFootball England — licencja CC0 w przypiętym commicie:** https://github.com/openfootball/england/blob/9ee7a0c351805c99cc334478a9bf04b7d0432fec/LICENSE.md
3. **OpenFootball España — licencja CC0 w przypiętym commicie:** https://github.com/openfootball/espana/blob/80035a93dd4920985af52aa097a54a6fb888563b/LICENSE.md
4. **OpenLigaDB / ODbL:** https://www.openligadb.de/lizenz — wcześniejsze wnioski i warunki osobno w [DANE_I_LICENCJE.md](DANE_I_LICENCJE.md).

## Co faktycznie wynika z regulaminu API-Football

- Operator dopuszcza budowanie **aplikacji i stron** przy użyciu API, ale zabrania bezpośredniej odsprzedaży dostarczanych danych i bezpośredniego konkurowania z jego ofertą danych bez pozwolenia.
- Operator **nie udziela licencji na publikację wszelkich danych, które dostarcza**, ani nie zapewnia praw do rozgrywek należących do organizatorów. Wskazuje, że odpowiednie licencje i zgody należy wyjaśnić u właścicieli praw.
- Serwisy dotyczące zakładów, fantasy sports i masowej dystrybucji mogą wymagać dodatkowych licencji. Nie wynika z tego automatycznie, czy i na jakich warunkach wolno publicznie pokazywać konkretne statystyki, wyniki, tabele albo prognozy algorytmiczne w RZOTKIEWCE AI.
- Logotypy i inne materiały identyfikacyjne mogą być chronione niezależnie od danych. **Dostęp w API nie jest licencją na ich użycie w marce lub produkcie.**
- Regulamin odróżnia abonament przez własny dashboard (prepaid z limitem dziennym) od RapidAPI (możliwe opłaty overage). Nie zmieniamy kanału płatności ani planu.

**Wniosek:** sam wykupiony PRO i technicznie poprawne zapytania nie stanowią wystarczającej podstawy prawnej do automatycznego uruchomienia płatnej prezentacji danych. Rozróżniać **wewnętrzne trenowanie/analizę**, **publiczne podawanie pojedynczych faktów i wyników**, **publikację większej bazy danych**, **odsprzedaż feedu** oraz **własną prognozę modelu**. Dla każdego sposobu użycia wymagane są osobne ustalenia.

## OpenFootball nie jest równoważne API-Football

Oba używane w badaniu archiwa OpenFootball zawierają licencję **CC0 1.0** w przypiętych commitach. Pozwala to korzystać z zadeklarowanych danych otwartego projektu na znacznie swobodniejszych warunkach niż z komercyjnego feedu. Nie gwarantuje jednak automatycznie poprawności terminarzy, zgody na cudze logotypy, braku innych praw organizatorów ani praw do rekordów API-Football. Nie mieszać surowych danych komercyjnego dostawcy z otwartym archiwum, by nadać im licencję CC0.

## Lista decyzji przed Premier League i LaLiga Premium

| Kategoria użycia | Stan | Co jest potrzebne |
| --- | --- | --- |
| Badania offline i własne testy modelu | TAK — nadal w trybie badawczym | Respektować regulamin i limity dostawców |
| Wyświetlanie pojedynczych terminów / wyników / statystyk API-Football | NIEUSTALONE | Pisemne wyjaśnienie praw i zakresu zastosowania |
| Sprzedaż dostępu do **własnych** prognoz 1X2 | NIEUSTALONE prawnie; technicznie bez walidacji jakości | Potwierdzić sposób korzystania z danych i dodatkowe prawa organizatorów; test prospektywny |
| Kopiowanie / redystrybucja hurtowa danych API | STOP | Bez odrębnego uprawnienia nie wdrażać |
| Logotypy lig i klubów / zdjęcia | STOP | Kontrola praw każdego materiału |
| 17 map ID OpenFootball ↔ API-Football | 0/17 zatwierdzonych | Indywidualny dowód łączenia identyfikatorów, nie tylko zgodność nazw |

W `data/identity_release_registry.json` pozostawiamy `rights_review_approved=false`, `release.requested=false` i 0 zatwierdzonych ID.

## Pytania do operatora przed komercyjnym startem (bez wysyłania)

1. Czy w płatnej aplikacji możemy udostępniać **własne prognozy** 1X2 opracowane z wykorzystaniem danych API, bez odsprzedaży feedu lub pełnych statystyk?
2. Jakie dane pojedynczych meczów (termin, uczestnicy, wynik, ograniczone statystyki) można pokazywać obok prognozy? Czy są warunki przypisania źródła, cache lub limitów wyświetlania?
3. Które prawa do Premier League i LaLiga oraz elementy brandingowe musimy uzyskać bezpośrednio od lig/klubów?
4. Czy istnieje osobna umowa lub oficjalne pisemne potwierdzenie dopuszczalnego modelu Premium?

**Nie zmieniamy:** `main`, strony, `predictions.json`, `lab_forward/`, modeli ani kluczy. Dalsza kontrola praw i ID jest konieczna **przed** planowaniem wdrożenia nowych lig.

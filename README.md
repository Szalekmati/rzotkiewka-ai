# 🫜 RZOTKIEWKA AI — strona 2.0

Wersja **2.0** oznacza **nowy interfejs**, nie nową wersję silnika prognoz. Panel startowy liczy statystyki z tych samych danych `predictions.json`, które zostały zweryfikowane w aplikacji; niczego nie dopisuje do archiwum. Jeśli plik nie przejdzie weryfikacji, panel nie pokazuje trafień.

Publiczny, eksperymentalny serwis z terminarzem piłkarskim, modelem prawdopodobieństw **1/X/2** i audytowalnym archiwum prognoz. Projekt korzysta z OpenLigaDB i publikuje statyczną stronę na GitHub Pages. **Nie gwarantuje wyników.**

## Co działa

- Prawdziwe terminarze i wyniki dla Bundesligi, 2. Bundesligi i 3. Ligi z OpenLigaDB (baza społecznościowa).
- Wyliczanie prawdopodobieństw 1/X/2 prostym modelem Poissona na podstawie dostępnej historii sezonu.
- Automatyczny zapis prognoz przed meczem w `predictions.json` (GitHub Actions co 6 godzin, bez gwarancji wykonania o dokładnej godzinie).
- Archiwizacja prognozy wraz z sumą SHA-256; strona przez HTTPS **rzeczywiście weryfikuje** sumy dla wyświetlanych rekordów.
- Rozliczanie wyników, także dla niezamkniętych prognoz z poprzednich sezonów (do 3 sezonów wstecz).
- Oddzielny test historyczny, jednoznacznie oznaczony jako retrospektywny.
- Fikcyjne typy **DEMO** w `tips.json`; widok planowanego Premium za 19,99 zł miesięcznie.

## Kontrola czasu meczów w audycie nowych lig

W audycie kandydatów (Premier League, LaLiga, Liga Mistrzów) wymagamy jednoznacznej daty i godziny `matchDateTimeUTC` z podaną strefą (`Z` lub przesunięcie `±HH:MM`). Dat lokalnych bez strefy nie wolno po cichu traktować jako UTC: taka pomyłka mogłaby przesunąć mecz oraz okna porównywania modeli. Niepoprawne daty obniżają kompletność danych w raporcie; nie są naprawiane przez zgadywanie. Kontrole pull request działają bez zapytań do zewnętrznego API, a istniejące zaplanowane audyty pozostają tylko badaniem źródeł: **nie dodają lig do aplikacji ani LAB automatycznie**.

## Paszport prognozy — prawdziwe dane wejściowe

Rozwijany **Paszport analizy** w zakładce Darmowe i kartach meczowych pokazuje nie tylko rozkład 1/X/2 i historię prognozy, ale także **wyprzedzenie zapisu przed planowanym początkiem spotkania**, liczbę wyników ligowych i meczów obu drużyn wykorzystanych w zapisanym snapshotcie, szacunki goli oraz możliwe do sprawdzenia identyfikatory meczów wejściowych. To **wyłącznie wartości faktycznie zachowane w zweryfikowanym archiwum** `predictions.json`; brakujące pola są oznaczane jako niedostępne, nie dopisywane. Czas zapisania nie jest niezależnym znacznikiem czasu, a skrót SHA-256 nie dowodzi dokładności źródła. Prognozowane gole to wynik modelu, **nie xG ze strzałów**. Paszport wyraźnie oddziela rekordy modelu 1.3 od niezależnego eksperymentu LAB 2.1/2.2. Nie odtwarzamy nieznanych wag ani powodu historycznej decyzji na podstawie współczesnych danych.

Kontrola jakości GitHub Actions dodatkowo uruchamia test `tests/test_prediction_passport.mjs` bez dostępu do sieci; potwierdza obecność danych wejściowych istniejącego archiwum oraz bezpieczny komunikat, gdy historyczne pola są niedostępne. Zamrożone modele, wyniki, statystyki całej próby i eksport CSV pozostają bez zmian.

## Katalog dostępnych i planowanych lig

Zakładka **Sporty i ligi** rozdziela rozgrywki z prawdziwie podłączonym źródłem danych od pozycji planowanych. Filtr **„Tylko podłączone ligi”** pokazuje obecnie trzy dostępne terminarze: Bundesliga, 2. Bundesliga i 3. Liga. Filtr współpracuje z wyszukiwaniem i wyborem dyscypliny, można go wyłączyć bez utraty pozostałych pozycji katalogu. Nie włącza nowych API, nie zmienia analizy meczów ani zamrożonych modeli LAB 2.1/2.2. Testy Chromium na małych ekranach sprawdzają, że wybranie dyscypliny bez danych nie powoduje fałszywej deklaracji dostępności.

## Darmowe prognozy i przyszły Premium

Zakładka **🔓 Darmowe** pokazuje realnie zapisane przed meczem prognozy 1/X/2, ich rozliczenia oraz całe archiwum (trafienia i pomyłki). Widok Premium jest planem produktu; płatności i bezpieczna kontrola dostępu nie działają. Plik `tips.json` zawiera wyłącznie fikcyjne rekordy DEMO — nie można przedstawiać ich jako historii skutecznych zakładów.

Pomysł produktowy: bezpłatna, możliwa do zweryfikowania próbka może pomagać użytkownikom ocenić usługę. Nie zakładamy wzrostu konwersji bez pomiaru. Statystyki trafień 1/X/2 nie są zwrotem z kuponów ani dowodem przewagi nad kursami. Przed uruchomieniem płatności i marketingu trzeba sprawdzić wymagania prawne i ograniczenia wiekowe.

## Bezpieczeństwo pełnej próby archiwum (fail-closed)

Publikowane wskaźniki muszą obejmować **wszystkie** zapisane rekordy, nie tylko te, które przeszły weryfikację. Po pobraniu `predictions.json` przeglądarka sprawdza SHA-256 **każdego** snapshotu, poprawność identyfikatorów i ich unikalność. Jeśli jeden rekord jest nieprawidłowy lub zduplikowany, **blokuje całe archiwum, wszystkie statystyki skuteczności, udostępnianie i eksport CSV** — zamiast pomijać błędny rekord. Repozytorium i modele pozostają niezmienione. Testy Node.js uruchamiają prawdziwe funkcje ładowania strony na danych prawidłowych, uszkodzonych i zduplikowanych. To wykrywanie niespójności danych, nie niezależne poświadczenie daty ich publikacji ani gwarancja trafności.

## Pobieranie całego archiwum CSV

Zakładka **Darmowe** udostępnia przycisk **Pobierz pełną historię CSV**. Przycisk jest aktywny dopiero po udanym pobraniu i weryfikacji SHA-256 wszystkich dopuszczonych rekordów. Eksport zawsze obejmuje **całe zweryfikowane archiwum, niezależnie od filtrów**, zarówno trafione, nietrafione, jak i oczekujące prognozy. Pola: data publikacji i startu, liga, drużyny, 1/X/2, wskazany lider, wynik meczu, rozliczenie, trafienie, Brier i pełny skrót SHA-256. Plik używa UTF-8, średników oraz zabezpieczenia przed wstrzyknięciem formuły do arkusza. Nie udostępnia kursów bukmacherskich, ROI ani gwarancji zysku.

## Udostępnianie zweryfikowanych prognoz

W zakładce **Darmowe** każda karta z publicznego, zweryfikowanego archiwum oferuje **Udostępnij analizę**. Na Androidzie otwiera systemowe udostępnianie, a w innych przeglądarkach próbuje skopiować link lub pokazuje okno ręcznego kopiowania. Link ma postać `?forecast=<identyfikator>#ranking`; odbiorca zobaczy wyróżniony, konkretny rekord tylko wtedy, gdy nadal znajduje się w archiwum po weryfikacji SHA-256. Dane nie są generowane ponownie ani ukrywane według wyniku. Brak kont, śledzenia kliknięć, kursów i obietnic zysku.

## Kontrola zgodności publicznego eksperymentu LAB

Zakładka **Test LAB** pokazuje bezpośredni odnośnik do ostatniego zapisanego uruchomienia GitHub Actions (tylko po zweryfikowaniu numerycznego `run_id`). Ponadto przed wyświetleniem liczników i porównania modeli pobiera **osobno** raport `lab_forward/RAPORT.md` i surowy `lab_forward/ledger.json`. Liczba zapisanych par musi być zgodna, a rejestr musi mieć oczekiwaną strukturę. Jeśli jeden plik jest nieosiągalny, ma nieznany format lub liczniki się różnią, strona ukrywa niepotwierdzone wyniki zamiast przedstawiać błędne zero. Użytkownik może sam otworzyć cały surowy rejestr, bez selekcji wyników. To **kontrola spójności plików, nie podpis kryptograficzny, niezależny dowód czasu publikacji ani potwierdzenie trafności**. Nie zmieniamy zamrożonego LAB, nie dodajemy prognoz wstecz i nie naruszamy archiwum produkcyjnego.

## Status automatyzacji LAB

Zakładka **Test LAB** w interfejsie strony 2.0 pokazuje teraz ostatnie *zapisane* zdarzenie z `lab_forward/run_status.json`: czas, rodzaj zdarzenia (ręczne lub `schedule`) i jego wynik. Jeśli status jest starszy niż 3 godziny, pojawia się ostrzeżenie i odnośnik do [historii GitHub Actions](https://github.com/Szalekmati/rzotkiewka-ai/actions/workflows/test_przedmeczowy.yml). **To nie jest odczyt bieżącego stanu GitHub Actions**, więc ostrzeżenie nie dowodzi awarii, a zielony test ręczny nie dowodzi sprawnego harmonogramu. Nie zmieniono zamrożonych silników 2.1/2.2, okna 162–168 h ani plików archiwum.

## Punkt odniesienia Brier na stronie (bez selekcji wyników)

Zakładka **Jakość modelu** pokazuje teraz średni błąd Brier zweryfikowanych, **rozliczonych** publicznych prognoz 1/X/2 obok prostego punktu odniesienia: stałych prawdopodobieństw 1/3, 1/3 i 1/3. W skali archiwum liczymy **średnią** trzech kwadratowych błędów — punkt odniesienia = **2/9 ≈ 0,222** (0 oznacza idealnie). W osobnym historycznym badaniu 2.1/2.2 LAB używamy **sumy** trzech błędów; jej punkt odniesienia to **2/3 ≈ 0,667**, czyli dokładnie trzy razy więcej. **Nie wolno porównywać tych wyników bez wyrównania skali i użycia tych samych spotkań.**

Dla małej liczby rozliczonych prognoz strona wyraźnie ostrzega o niepewności. Nie podaje ROI, nie wybiera korzystnych meczów i nie przedstawia porównania z naiwną prognozą jako dowodu przewagi nad bukmacherem. Cała analiza pozostaje oparta na wcześniej zweryfikowanym archiwum SHA-256, bez modyfikacji modeli i zapisów LAB. Testy zabezpieczają wzór i obecność ostrzeżenia.

## Kontrola jakości strony

Automatyczne testy na GitHubie sprawdzają unikalne identyfikatory HTML, domyślne filtry darmowych prognoz bez pomijania porażek, etykiety DEMO/Premium, integralność archiwum i składnię JavaScript (Node.js). Kontrola uruchamia się po zmianach strony lub danych, nie pobiera kursów ani nie wykonuje transakcji. Wymaga Node.js tylko do testu JavaScript; bez Node ten test lokalnie jest pomijany. Zielony test nie zastępuje sprawdzenia strony w przeglądarce i nie blokuje automatycznie publikacji GitHub Pages.

## Zapasowe uruchamianie LAB po automatycznym zadaniu produkcyjnym

LAB korzysta obecnie z trzech sposobów uruchomienia: własny harmonogram `37 * * * *` (UTC), ręczne `workflow_dispatch` i **zapasowe `workflow_run`** po pomyślnym *zaplanowanym* (nie ręcznym) przebiegu workflow `RZOTKIEWKA - prognozy i wyniki 1.6` na domyślnej gałęzi `main`. Kod nie pobiera i nie uruchamia artefaktów procesu źródłowego; kontroluje jego wynik, typ wyzwalacza, gałąź i repozytorium. Wszystkie starty LAB dzielą jedną kolejkę `concurrency`, nie zmieniając zamrożonych silników ani okna 162–168 h. Dodatkowe uruchomienia GitHub Actions mogą zużywać minuty z limitu konta; ten mechanizm nie gwarantuje dostarczenia wyzwalacza i nie jest niezależnym zewnętrznym harmonogramem. Strona odróżnia zapis `schedule`, zapasowy `workflow_run` i uruchomienie ręczne.

## Ochrona eksperymentu LAB 2.1/2.2

Test `tests/test_lab_schedule.py` pilnuje konfiguracji harmonogramu (37. minuta godziny, także ręczny fallback), zamrożonej paczki modeli po SHA-256, sztywnego okna 162–168 h przed meczem oraz zapisu statusu uruchomienia. Jest wykonywany przez istniejącą kontrolę jakości po zmianach konfiguracji, bez pobierania danych i bez generowania prognoz. **Zielony test oznacza zgodność kodu, nie dostarczenie zdarzenia `schedule` przez GitHub**. Problemy z działaniem samego harmonogramu śledzimy w [zadaniu #1](https://github.com/Szalekmati/rzotkiewka-ai/issues/1).

## Czego jeszcze nie ma

- Prawdziwych płatności, kont ani bezpiecznej blokady Premium.
- Potwierdzonej skuteczności modelu na dużej próbce zapisanych *przed meczami* prognoz.
- Automatycznego pobierania kursów bukmacherskich ani gwarancji opłacalności zakładów.

## Wgranie na GitHub (telefon lub komputer)

1. Rozpakuj pobrane archiwum ZIP.
2. W repozytorium `Szalekmati/rzotkiewka-ai` wgraj **pliki z tej paczki aktualizacyjnej** do odpowiadających im ścieżek (plik `index.html` w katalogu głównym, plik YAML do `.github/workflows/`, testy do `tests/`).
3. Zastąp tylko pliki obecne w paczce i zatwierdź przez `Commit changes`. **Nie usuwaj `predictions.json` ani `tips.json`.**
4. W zakładce **Actions** uruchom ręcznie `RZOTKIEWKA - archiwum prognoz`, jeżeli chcesz od razu sprawdzić aktualizację. Normalnie harmonogram działa automatycznie.
5. Otwórz stronę GitHub Pages po udanym wdrożeniu. Archiwum na stronie jest ładowane z własnego `predictions.json`.

**Ważne:** paczka aktualizacyjna celowo **nie zawiera `predictions.json` ani `tips.json`**, żeby nie nadpisać nowych prognoz wygenerowanych przez GitHub Actions. Zachowaj obydwa istniejące pliki w repozytorium.

## Uruchamianie lokalnie

```bash
python -m unittest discover -s tests -v
python forecast_engine.py
python -m http.server 8000
```

Otwórz `http://localhost:8000`. W przeglądarce na adresie HTTP bez HTTPS (poza localhost) weryfikacja kryptograficzna może być niedostępna. `forecast_engine.py` wymaga dostępu do internetu, ale testy są offline. Nie wpisuj kluczy API ani danych portfeli do repozytorium.

## Integralność archiwum

Suma SHA-256 wykrywa przypadkową lub nieautoryzowaną modyfikację prognozy względem zapisanej sumy, ale **właściciel repozytorium może zmienić zarówno prognozę, jak i jej sumę**; niezależnym potwierdzeniem chronologii jest historia publicznych commitów, która również może być przepisana przez administratora. To nie jest niezależny audyt i nie potwierdza przewagi statystycznej.

Model statystyczny zachowuje oznaczenie `1.3.0`, ponieważ w wydaniu 1.4 poprawiono niezawodność i kontrolę danych, **nie zmieniono samej formuły**. Starsze zapisane prognozy pozostają bez modyfikacji.

Źródło danych: [OpenLigaDB](https://www.openligadb.de/) — licencja [ODbL 1.0](https://www.openligadb.de/lizenz). Komercyjne wykorzystanie danych jest dozwolone z zachowaniem warunków licencji, w tym widocznego oznaczenia źródła; reguły publicznego udostępniania zmodyfikowanych baz wymagają odrębnej uwagi. **Obecny interfejs pobiera dane bezpośrednio z przeglądarek** — przed większym ruchem i Premium konieczny jest centralny cache zgodny z [warunkami API](https://www.openligadb.de/nutzungsbedingungen). Przed wdrożeniem zapoznaj się z [zasadami danych i licencji](docs/DANE_I_LICENCJE.md). Herby i logo klubów nie są objęte licencją danych. Serwis 18+; obstawianie zakładów wiąże się z możliwością straty pieniędzy.

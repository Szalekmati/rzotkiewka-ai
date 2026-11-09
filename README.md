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

## Darmowe prognozy i przyszły Premium

Zakładka **🔓 Darmowe** pokazuje realnie zapisane przed meczem prognozy 1/X/2, ich rozliczenia oraz całe archiwum (trafienia i pomyłki). Widok Premium jest planem produktu; płatności i bezpieczna kontrola dostępu nie działają. Plik `tips.json` zawiera wyłącznie fikcyjne rekordy DEMO — nie można przedstawiać ich jako historii skutecznych zakładów.

Pomysł produktowy: bezpłatna, możliwa do zweryfikowania próbka może pomagać użytkownikom ocenić usługę. Nie zakładamy wzrostu konwersji bez pomiaru. Statystyki trafień 1/X/2 nie są zwrotem z kuponów ani dowodem przewagi nad kursami. Przed uruchomieniem płatności i marketingu trzeba sprawdzić wymagania prawne i ograniczenia wiekowe.

## Udostępnianie zweryfikowanych prognoz

W zakładce **Darmowe** każda karta z publicznego, zweryfikowanego archiwum oferuje **Udostępnij analizę**. Na Androidzie otwiera systemowe udostępnianie, a w innych przeglądarkach próbuje skopiować link lub pokazuje okno ręcznego kopiowania. Link ma postać `?forecast=<identyfikator>#ranking`; odbiorca zobaczy wyróżniony, konkretny rekord tylko wtedy, gdy nadal znajduje się w archiwum po weryfikacji SHA-256. Dane nie są generowane ponownie ani ukrywane według wyniku. Brak kont, śledzenia kliknięć, kursów i obietnic zysku.

## Kontrola jakości strony

Automatyczne testy na GitHubie sprawdzają unikalne identyfikatory HTML, domyślne filtry darmowych prognoz bez pomijania porażek, etykiety DEMO/Premium, integralność archiwum i składnię JavaScript (Node.js). Kontrola uruchamia się po zmianach strony lub danych, nie pobiera kursów ani nie wykonuje transakcji. Wymaga Node.js tylko do testu JavaScript; bez Node ten test lokalnie jest pomijany. Zielony test nie zastępuje sprawdzenia strony w przeglądarce i nie blokuje automatycznie publikacji GitHub Pages.

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

Źródło danych: [OpenLigaDB](https://www.openligadb.de/). Przy dalszym publicznym wykorzystaniu sprawdź warunki licencji ODbL 1.0, w tym obowiązki atrybucji i ewentualnego udostępniania danych pochodnych. Serwis 18+; obstawianie zakładów wiąże się z możliwością straty pieniędzy.

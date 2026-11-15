# RZOTKIEWKA AI — plan próbnej publikacji i rollback (bez wdrożenia)

Data: 15 listopada 2026. Dokument pomocniczy do [issue #38](https://github.com/Szalekmati/rzotkiewka-ai/issues/38). Ta gałąź **nie przełącza GitHub Pages**.

## Potwierdzona przyczyna zbędnych buildów

Commity `ac78286` i `b22cdc6` zmieniały wyłącznie `lab_forward/RAPORT.md` oraz `lab_forward/run_status.json`. Mimo `[skip ci]` w komunikacie commita uruchomiły się dopasowane po `head_sha` wdrożenia Pages [#43699413499](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43699413499) oraz [#43701220970](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43701220970). To dwa potwierdzone przykłady, nie dowód, że wszystkie publikacje są zbędne.

## Co musi być publikowane

Strona odwołuje się lokalnie do: `predictions.json`, `tips.json`, `lab_forward/ledger.json`, `lab_forward/experiment.json`, `lab_forward/run_status.json` i `lab_forward/RAPORT.md`.

Podgląd przygotowuje również `index.html` oraz `CNAME` z domeną `rzotkiewka.pl`. Brak choć jednego wymaganego pliku lub nowe nieujęte odwołanie zatrzymuje przygotowanie. Narzędzie `tools/prepare_pages_bundle.py` kopiuje dokładne bajty i weryfikuje SHA-256, ale **nie publikuje plików** i nie zastępuje pełnej walidacji zawartości prognoz.

Opcjonalny, wyłącznie lokalny dry-run:

```sh
python tools/prepare_pages_bundle.py /tmp/rzotkiewka-pages-preview-20261115
python -m unittest discover -s tests -p 'test_pages_bundle.py' -v
```

Ścieżka wyjściowa musi jeszcze nie istnieć i znajdować się poza repo. Program nie nadpisuje istniejących danych.

## Rozstrzygnięcie wymagane przed migracją

Możliwe przyszłe rozwiązanie: publikacja GitHub Pages z dedykowanego workflow uruchamianego po zmianach plików publicznych, a nie każdym commicie LAB. **Nie wdrażamy go teraz.**

Uwaga: pominięcie zmian `run_status.json` i `RAPORT.md` jako wyzwalaczy może oznaczać **nieaktualny status LAB na stronie**, nawet jeśli skan faktycznie się zakończył. Przed migracją trzeba wybrać i przetestować sposób jasnego wyświetlania wieku publikowanych danych; alternatywnie pozostawić status jako wyzwalacz i zaakceptować mniejsze oszczędności. Bez tego nie przełączamy publikacji.

## Bramki migracji

1. Potwierdzić ręcznie w `Settings > Pages` rzeczywisty mechanizm publikacji, gałąź/katalog, `Custom domain` i HTTPS. Nie ustalaliśmy tych wartości przez uprawnioną API.
2. Sprawdzić dostępność `rzotkiewka.pl` i `www` (jeśli skonfigurowane), DNS, przekierowania i zachowanie certyfikatu. Nie ruszać rekordów pocztowych i serwerów nazw OVHcloud.
3. Zweryfikować, że zachowane są wszystkie pliki i zachowanie sekcji LAB oraz prognoz; uruchomić dotychczasowe testy mobilne, JS i archiwum.
4. Uzgodnić odświeżanie statusu LAB i przetestować je na kopii. Nie mylić pomyślnego CI z aktualnością publicznych danych.
5. W osobnym PR i po osobnej zgodzie zaprojektować workflow deploy wyłącznie dla `main`, z wymaganymi uprawnieniami `pages: write`, `id-token: write`, bez publikacji z PR, bez nowego crona. Nie uruchamiać ani nie przełączać `Settings > Pages` podczas przeglądu.
6. Przełączenie i próby publiczne wykonać w kontrolowanym oknie. Zachować ustawienie własnej domeny w `Settings > Pages`; sam plik CNAME nie wystarczy w publikacji przez Actions.

## Plan wycofania

Przed przełączeniem zapisać poprzednie źródło publikacji (gałąź/katalog), domenę, DNS i commit produkcyjny. Przy awarii przywrócić poprzednie źródło Pages, wycofać nowy workflow kontrolowaną zmianą i sprawdzić HTTPS, przekierowania, archiwum i wszystkie zasoby LAB. Nie obiecywać zerowego przestoju.

**Granice tego PR:** tylko kod przygotowania kopii, testy i dokumentacja. Nie zmienia modelu, LAB, archiwum, domeny, aktualnego źródła Pages, harmonogramów, ani kosztów/subskrypcji.

Dokumentacja: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Aktualizacja po wdrożeniu #40 — 15.11.2026

Monitor LAB z [PR #40](https://github.com/Szalekmati/rzotkiewka-ai/pull/40) jest już scalony z gałęzią `main`. Historyczna gałąź #41 zawierała jego identyczne pliki z wcześniejszej próby integracyjnej. **Przed scaleniem #41 obowiązuje weryfikacja łączna z obecnym `main`**, w szczególności dwa niezależne kroki CI dla monitora LAB i próbnego pakietu Pages, a także brak usunięć wśród plików LAB.

Test `test_ci_retains_both_readonly_quality_gates` chroni oba kroki i filtry CI. Publikacja GitHub Pages będzie wymagała odrębnej decyzji i osobnego planu uwzględniającego aktualność wyświetlanego statusu LAB.

**Nadal nie wdrażamy filtrowanej publikacji Pages**, nie zmieniamy źródła wdrożenia, nie wyłączamy automatycznych LAB i nie obiecujemy oszczędności, dopóki nie zostaną zmierzone po osobno zatwierdzonej migracji.

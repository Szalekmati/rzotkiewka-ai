# Gotowy do przeglądu projekt workflow — NIEAKTYWNY

Ten plik: `docs/PAGES_ACTIONS_CANDIDATE.yml`. **Nie jest** workflow. GitHub Actions szuka workflow wyłącznie pod `.github/workflows/`, więc umieszczenie go w `docs/` nie uruchomi wdrożenia.

## Projekt bezpiecznej migracji

1. Zabezpieczyć bieżące ustawienia w GitHub **Settings > Pages**: `Source`, `Custom domain`, `Enforce HTTPS`, bazową gałąź i katalog. Zapisać obecną treść DNS w OVHcloud (nie zmieniać rekordów poczty).
2. Potwierdzić, że działająca domena `rzotkiewka.pl` i ewentualne `www` wskazują poprawnie, a `index.html`, `predictions.json`, `tips.json`, wszystkie cztery pliki LAB i certyfikat HTTPS odpowiadają. Nie twierdzić, że stronę zweryfikowano, jeśli tylko zadziałało CI.
3. Dopiero po **osobnym, jednoznacznym zatwierdzeniu** umieścić zweryfikowaną kopię `PAGES_ACTIONS_CANDIDATE.yml` w `.github/workflows/pages_deploy.yml`. Konieczny przegląd uprawnień `pages: write` i `id-token: write`, ochrony środowiska `github-pages`, oraz ponowny pełny CI.
4. W uzgodnionym oknie przełączyć ręcznie `Settings > Pages > Build and deployment > Source` z obecnego źródła na **GitHub Actions**. Nie wybierać szablonu, który równolegle publikuje z katalogu repo. Zachować istniejącą własną domenę wpisaną w **Settings > Pages**, bo sam `CNAME` nie konfiguruje jej w trybie Actions.
5. Uruchomić pierwszy kontrolowany `workflow_dispatch` na `main`, sprawdzić jego krok `deploy`, stronę publiczną, HTTPS i wszystkie zasoby. Sprawdzić, czy zmiana tylko testów/dokumentacji *nie* powoduje Pages run; zmiana `index.html`, statusu LAB i narzędzia `prepare_pages_bundle.py` *powinna* powodować run.
6. Zmierzyć faktyczne minuty GitHub Actions/Pages przez kilka dni i porównać je z analogicznym okresem przed zmianą. Nie zakładać oszczędności bez tych liczb. Przy obecnej zasadzie publikowania status-only nie ograniczamy ich kosztu — pomijamy **tylko** zmiany techniczne.

## Gwarancja zachowania LAB

Filtr wymienia obydwa pliki statusu: `lab_forward/run_status.json` i `lab_forward/RAPORT.md`. **Zapisana obserwacja nadal musi się publikować**. Rozdzielony `LAB 2.1/2.2` nie jest przez ten projekt uruchamiany, zatrzymywany, oceniany ani promowany. Polecenie `tools/prepare_pages_bundle.py` kopiuje i sprawdza bajt po bajcie osiem plików, a nie całe repo.

Ręczne wywołanie `workflow_dispatch` w proponowanym workflow jest zablokowane poza `main`; PR nigdy nie wywołuje wdrożenia. Nieznany nowy zasób wymaga ręcznego dodania go do `PUBLIC_FILES`, filtra i testów przed aktywacją.

## Rollback

W razie błędów wdrożenia, domeny lub niewłaściwych danych LAB: zatrzymać nowy mechanizm, przywrócić wcześniej zapisane `Settings > Pages > Source` i dotychczasową gałąź/katalog; przywrócić oryginalne ustawienia własnej domeny i HTTPS, usunąć nowy aktywny workflow w **osobnej, kontrolowanej zmianie**. Sprawdzić pełną stronę, rozliczenia, raport i archiwum. Zmiana źródła może powodować przerwę. **Nie zmieniać DNS bez osobnego planu**.

## Ograniczenia

To **projekt**, nie gotowe działające wdrożenie. Nie sprawdza dostępności domeny, ustawień Pages (wymagają uprawnień właściciela) ani nie mierzy oszczędności. Ma służyć do przeglądu i testów offline. Brak zgody na uruchomienie usług płatnych i zmianę serwowania witryny.

Dokumentacja:
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

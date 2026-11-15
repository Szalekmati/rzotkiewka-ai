# RZOTKIEWKA AI — klasyfikacja zmian Pages (wyłącznie test)

Data: 15 listopada 2026. Uzupełnienie issue #38 i planu docs/PAGES_PLAN_DRY_RUN.md.

## Potwierdzone fakty

- Zmiany wyłącznie statusu LAB w commitach ac78286 i b22cdc6 wywołały Pages build: uruchomienia 43699413499 i 43701220970.
- Poprawka #42 zmieniła wyłącznie narzędzia, dokumentację i workflow jakości, a mimo to uruchomiła Pages build 43733964537.
- W obecnej konfiguracji samo filtrowanie ścieżek w quality_site.yml nie steruje automatycznym GitHub Pages. Publikacja przez GitHub Actions z własnym filtrem wymaga odrębnej konfiguracji źródła Pages.

## Wykorzystanie narzędzia (nie publikuje niczego)

W katalogu repozytorium:

    python -m tools.pages_change_impact index.html tests/test_site_integrity.py
    python -m tools.pages_change_impact lab_forward/RAPORT.md lab_forward/run_status.json
    python -m tools.pages_change_impact --allow-stale-lab lab_forward/RAPORT.md lab_forward/run_status.json
    python -m tools.pages_change_impact .github/workflows/quality_site.yml

Wyniki symulacji:

- PUBLISH_CANDIDATE: zasób witryny (HTML, predictions.json, tips.json, ledger/config LAB, CNAME) lub raport/status LAB w domyślnej, bezpiecznej polityce aktualności
- SKIP_CANDIDATE_STALE_LAB: tylko gdy symulacja jawnie dopuszcza nieaktualny opublikowany raport/status LAB; panel #43 może ostrzegać o wieku, ale nie odzyskuje aktualnych danych
- SKIP_CANDIDATE_TECHNICAL: tylko zmiany pod tests/, docs/ lub tools/, bez zmian ośmiu publicznych plików, w hipotetycznym docelowym pakiecie
- REVIEW_UNKNOWN: nieznana ścieżka lub jakikolwiek workflow .github/workflows/. Nie zgadywać i nie pomijać automatycznie.

Narzędzie bierze wyłącznie ręcznie przekazaną listę ścieżek. NIE wykonuje wdrożenia, żadnych modyfikacji, żądań sieciowych lub odczytów GitHub. Nie mierzy oszczędności. Nie stanowi mechanizmu do automatycznego podjęcia decyzji o publikacji.

## Co musi się wydarzyć przed realną migracją

1. Potwierdzić przez właściciela obecne Settings > Pages > Source, Custom domain oraz HTTPS. Nie przełączać w tym PR.
2. Wybrać politykę aktualności LAB. Bezpieczna wartość domyślna: zachowanie publikacji przy każdej zmianie statusu LAB. Akceptacja nieaktualnych opublikowanych statusów wymaga osobnej decyzji.
3. Dopiero w osobnym, zatwierdzonym PR przygotować GitHub Actions deployment dla main z uprawnieniami pages: write / id-token: write, ochroną środowiska github-pages i sprawdzonymi filtrami. Nie wdrażać z PR.
4. Przetestować pod własną domeną, z HTTPS, wszystkimi linkami, archiwum, raportami i LAB, z planem wycofania.
5. Porównać rzeczywiste liczby wdrożeń i minuty rozliczeniowe przed i po. Na razie nie ma pomiaru oszczędności.

Przy GitHub Actions sam plik CNAME nie ustanawia domeny: musi zostać poprawnie zapisana w Settings > Pages. Nie modyfikować DNS poczty ani serwerów nazw.

Źródła:
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow

Tylko dry-run. Nie uruchamia żadnego planu płatnego, nowego harmonogramu ani publikacji.

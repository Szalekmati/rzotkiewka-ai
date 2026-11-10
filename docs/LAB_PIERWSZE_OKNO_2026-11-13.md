# LAB 2.1 / 2.2 — kontrola pierwszego okna (13 listopada 2026)

**Cel:** potwierdzić prawdziwy, niezmienny zapis par prognoz przed meczami — nie tylko zieloną ikonę GitHub Actions.

## Kontrakt eksperymentu (nie zmieniać podczas obserwacji)

- `lab_forward/experiment.json`: `min_lead_hours=162`, `max_lead_hours=168`; modele i kalibracja zamrożone.
- Wymagany jest zapis *przed rozpoczęciem meczu*, w faktycznym oknie 162–168 h do rozpoczęcia.
- Modele v21 i v22_lab muszą mieć wpisy dla tej samej pary meczowej; pierwszych prognoz nie nadpisywać.
- Nie liczyć skuteczności z 0 rozliczonych par, nie używać backfillów jako dowodu prognozy na żywo.
- Wynik `success` w Actions dowodzi wykonania zadania, **nie** potwierdza zapisania prognoz.

## Punkt startowy (sprawdzone 10 listopada 2026)

- Ostatni zapis `lab_forward/run_status.json`: `2026-11-10T12:40:28Z`, `event=workflow_run`, `upstream_event=schedule`, `observation_outcome=success`.
- `lab_forward/RAPORT.md`: 0 zapisanych par i 0 rozliczeń.
- Oczekiwane (historyczna diagnostyka) pierwsze otwarcie: **13 listopada 2026, około 18:30 czasu polskiego**, do około 00:30 dnia następnego. To nie jest gwarantowany termin: przed kontrolą ponownie sprawdzić terminarz.
- Godzinowe próby `37 * * * *` UTC mogą się spóźniać lub nie uruchomić. Ścieżka zapasowa `workflow_run` wymaga udanego zaplanowanego zadania produkcyjnego.

## Kontrola przed i w czasie okna

1. Sprawdź [Actions: Test przedmeczowy LAB](https://github.com/Szalekmati/rzotkiewka-ai/actions/workflows/test_przedmeczowy.yml); odróżnij uruchomienia `schedule`, `workflow_run` i `workflow_dispatch`. Nie traktuj udanego ręcznego startu jako dowodu działania harmonogramu.
2. Otwórz [status](../lab_forward/run_status.json), [raport](../lab_forward/RAPORT.md), [ledger](../lab_forward/ledger.json) i historię commitów `main`. Porównaj czas oraz typ zdarzenia, liczbę par, błędy i commit zapisujący wynik.
3. Zweryfikuj w aktualnym terminarzu, że spotkanie rzeczywiście znajduje się **162–168 godzin przed startem**. Nie uznawaj samego planowanego otwarcia okna za gwarancję zapisania prognozy.
4. Przy braku zapisu w aktywnym oknie sprawdź brakujące dane historyczne obu modeli, API, logi, status workflow i konflikty zapisu git. Jeśli automat nie działa, dopuszczalne jest ręczne `Run workflow` **tylko w nadal otwartym oknie**, a potem potwierdzenie commitu — bez fałszowania czasu zdarzenia.
5. Po zapisie sprawdź niezmienność pierwszych prognoz i parowanie v21/v22_lab. Jeśli mecz został przełożony lub zmieniono drużyny, oznacz go zgodnie z protokołem, zamiast dopasowywać stare przewidywania.
6. Po rozegraniu meczów ocena wymaga potwierdzonego wyniku oraz minimum 3 h od rozpoczęcia. Dopiero wtedy można liczyć trafność, Brier i log loss. Przegląd po 300 rozliczonych parach — nie wcześniej jako ostateczny werdykt.

## Rozróżnienie czterech wyników kontroli

| Stan | Interpretacja | Następny krok |
| --- | --- | --- |
| Zadanie nie uruchomiło się | Ryzyko utraty okna | Sprawdź harmonogram i ścieżkę zapasową; podczas okna ręczne uruchomienie |
| Zadanie zielone, 0 par, brak meczów w oknie | Prawidłowy pusty skan | Sprawdź następne okno, nie dopisuj fikcyjnych prognoz |
| Zadanie zielone, mecze w oknie, 0 par | Potencjalny problem z danymi/kwalifikacją | Sprawdź `RAPORT.md`, logi i dostępność historii obu modeli |
| Ledger ma pary z commitem sprzed spotkania | Pierwszy rzeczywisty zapis | Zachowaj dowód czasu; czekaj na oficjalne rozliczenia |

Zgłoszenie nadzorcze: [issue #1](https://github.com/Szalekmati/rzotkiewka-ai/issues/1).

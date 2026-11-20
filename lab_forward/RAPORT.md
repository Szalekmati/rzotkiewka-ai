# RZOTKIEWKA — test przedmeczowy 2.1 / 2.2 LAB

Ostatnia obserwacja UTC: 2026-11-20T21:50:43.133885Z

Prognozy: 162–168 godzin przed meczem. Pierwszy zapis jest niezmienny.
Ten protokół różni się od retrospektywnego testu dokładnie 168 h przed meczem.

Zapisane pary prognoz: 32.

| Liga | Model | Rozliczone | Trafność | Brier ↓ | Log loss ↓ |
|---|---|---:|---:|---:|---:|
| Razem | v21 | 3 | 66.67% | 0.52478 | 0.89342 |
| Razem | v22_lab | 3 | 66.67% | 0.56173 | 0.94901 |
| bl1 | v21 | 0 | — | — | — |
| bl1 | v22_lab | 0 | — | — | — |
| bl2 | v21 | 2 | 50.00% | 0.62039 | 1.02194 |
| bl2 | v22_lab | 2 | 50.00% | 0.63835 | 1.05553 |
| bl3 | v21 | 1 | 100.00% | 0.33356 | 0.63637 |
| bl3 | v22_lab | 1 | 100.00% | 0.40848 | 0.73596 |

Wyłączone po zmianie terminu lub drużyn: 0.

Parametry LAB pochodzą z kalibracji 2024/25. Bez ponownego dopasowywania.
Rozliczenia wymagają zaakceptowanego wyniku i minimum 3 h od rozpoczęcia.
Korekty wyników są dopisywane jako nowe obserwacje; raport używa najnowszej.
Kopie wejść i skróty pomagają kontrolować zmiany. Historia commitów jest dowodem czasu publikacji; sam hash nie jest zewnętrznym znacznikiem czasu.
Brak prognozy nie jest liczony jako nietrafiony typ. Nie zmieniamy silnika produkcyjnego.
Wyniki nie mierzą ROI. Mała próba nie rozstrzyga przewagi modelu.

## Błędy pobierania


## Pominięte w bieżącym uruchomieniu


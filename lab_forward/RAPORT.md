# RZOTKIEWKA — test przedmeczowy 2.1 / 2.2 LAB

Ostatnia obserwacja UTC: 2026-11-22T17:51:08.219673Z

Prognozy: 162–168 godzin przed meczem. Pierwszy zapis jest niezmienny.
Ten protokół różni się od retrospektywnego testu dokładnie 168 h przed meczem.

Zapisane pary prognoz: 54.

| Liga | Model | Rozliczone | Trafność | Brier ↓ | Log loss ↓ |
|---|---|---:|---:|---:|---:|
| Razem | v21 | 25 | 64.00% | 0.56272 | 0.94810 |
| Razem | v22_lab | 25 | 64.00% | 0.56748 | 0.95509 |
| bl1 | v21 | 8 | 50.00% | 0.62112 | 1.01830 |
| bl1 | v22_lab | 8 | 50.00% | 0.61940 | 1.01707 |
| bl2 | v21 | 9 | 55.56% | 0.61016 | 1.02051 |
| bl2 | v22_lab | 9 | 55.56% | 0.61575 | 1.02852 |
| bl3 | v21 | 8 | 87.50% | 0.45096 | 0.79645 |
| bl3 | v22_lab | 8 | 87.50% | 0.46127 | 0.81051 |

Wyłączone po zmianie terminu lub drużyn: 0.

Parametry LAB pochodzą z kalibracji 2024/25. Bez ponownego dopasowywania.
Rozliczenia wymagają zaakceptowanego wyniku i minimum 3 h od rozpoczęcia.
Korekty wyników są dopisywane jako nowe obserwacje; raport używa najnowszej.
Kopie wejść i skróty pomagają kontrolować zmiany. Historia commitów jest dowodem czasu publikacji; sam hash nie jest zewnętrznym znacznikiem czasu.
Brak prognozy nie jest liczony jako nietrafiony typ. Nie zmieniamy silnika produkcyjnego.
Wyniki nie mierzą ROI. Mała próba nie rozstrzyga przewagi modelu.

## Błędy pobierania


## Pominięte w bieżącym uruchomieniu


# RZOTKIEWKA — test przedmeczowy 2.1 / 2.2 LAB

Ostatnia obserwacja UTC: 2026-11-22T09:52:01.921497Z

Prognozy: 162–168 godzin przed meczem. Pierwszy zapis jest niezmienny.
Ten protokół różni się od retrospektywnego testu dokładnie 168 h przed meczem.

Zapisane pary prognoz: 47.

| Liga | Model | Rozliczone | Trafność | Brier ↓ | Log loss ↓ |
|---|---|---:|---:|---:|---:|
| Razem | v21 | 20 | 70.00% | 0.54191 | 0.92037 |
| Razem | v22_lab | 20 | 70.00% | 0.55061 | 0.93389 |
| bl1 | v21 | 7 | 57.14% | 0.62709 | 1.02838 |
| bl1 | v22_lab | 7 | 57.14% | 0.62150 | 1.02178 |
| bl2 | v21 | 6 | 66.67% | 0.55790 | 0.94984 |
| bl2 | v22_lab | 6 | 66.67% | 0.57689 | 0.98084 |
| bl3 | v21 | 7 | 85.71% | 0.44303 | 0.78711 |
| bl3 | v22_lab | 7 | 85.71% | 0.45720 | 0.80577 |

Wyłączone po zmianie terminu lub drużyn: 0.

Parametry LAB pochodzą z kalibracji 2024/25. Bez ponownego dopasowywania.
Rozliczenia wymagają zaakceptowanego wyniku i minimum 3 h od rozpoczęcia.
Korekty wyników są dopisywane jako nowe obserwacje; raport używa najnowszej.
Kopie wejść i skróty pomagają kontrolować zmiany. Historia commitów jest dowodem czasu publikacji; sam hash nie jest zewnętrznym znacznikiem czasu.
Brak prognozy nie jest liczony jako nietrafiony typ. Nie zmieniamy silnika produkcyjnego.
Wyniki nie mierzą ROI. Mała próba nie rozstrzyga przewagi modelu.

## Błędy pobierania


## Pominięte w bieżącym uruchomieniu


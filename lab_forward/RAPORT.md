# RZOTKIEWKA — test przedmeczowy 2.1 / 2.2 LAB

Ostatnia obserwacja UTC: 2026-11-28T16:54:20.125227Z

Prognozy: 162–168 godzin przed meczem. Pierwszy zapis jest niezmienny.
Ten protokół różni się od retrospektywnego testu dokładnie 168 h przed meczem.

Zapisane pary prognoz: 74.

| Liga | Model | Rozliczone | Trafność | Brier ↓ | Log loss ↓ |
|---|---|---:|---:|---:|---:|
| Razem | v21 | 40 | 60.00% | 0.55930 | 0.94562 |
| Razem | v22_lab | 40 | 62.50% | 0.56299 | 0.95088 |
| bl1 | v21 | 10 | 50.00% | 0.62728 | 1.02949 |
| bl1 | v22_lab | 10 | 50.00% | 0.62419 | 1.02675 |
| bl2 | v21 | 14 | 64.29% | 0.52890 | 0.90662 |
| bl2 | v22_lab | 14 | 64.29% | 0.54467 | 0.92875 |
| bl3 | v21 | 16 | 62.50% | 0.54340 | 0.92731 |
| bl3 | v22_lab | 16 | 68.75% | 0.54077 | 0.92284 |

Wyłączone po zmianie terminu lub drużyn: 0.

Parametry LAB pochodzą z kalibracji 2024/25. Bez ponownego dopasowywania.
Rozliczenia wymagają zaakceptowanego wyniku i minimum 3 h od rozpoczęcia.
Korekty wyników są dopisywane jako nowe obserwacje; raport używa najnowszej.
Kopie wejść i skróty pomagają kontrolować zmiany. Historia commitów jest dowodem czasu publikacji; sam hash nie jest zewnętrznym znacznikiem czasu.
Brak prognozy nie jest liczony jako nietrafiony typ. Nie zmieniamy silnika produkcyjnego.
Wyniki nie mierzą ROI. Mała próba nie rozstrzyga przewagi modelu.

## Błędy pobierania


## Pominięte w bieżącym uruchomieniu


# RZOTKIEWKA — test przedmeczowy 2.1 / 2.2 LAB

Ostatnia obserwacja UTC: 2026-11-28T14:29:01.833058Z

Prognozy: 162–168 godzin przed meczem. Pierwszy zapis jest niezmienny.
Ten protokół różni się od retrospektywnego testu dokładnie 168 h przed meczem.

Zapisane pary prognoz: 68.

| Liga | Model | Rozliczone | Trafność | Brier ↓ | Log loss ↓ |
|---|---|---:|---:|---:|---:|
| Razem | v21 | 32 | 62.50% | 0.55479 | 0.93664 |
| Razem | v22_lab | 32 | 62.50% | 0.55756 | 0.94152 |
| bl1 | v21 | 10 | 50.00% | 0.62728 | 1.02949 |
| bl1 | v22_lab | 10 | 50.00% | 0.62419 | 1.02675 |
| bl2 | v21 | 11 | 54.55% | 0.57744 | 0.97425 |
| bl2 | v22_lab | 11 | 54.55% | 0.58659 | 0.98758 |
| bl3 | v21 | 11 | 81.82% | 0.46623 | 0.81462 |
| bl3 | v22_lab | 11 | 81.82% | 0.46795 | 0.81799 |

Wyłączone po zmianie terminu lub drużyn: 0.

Parametry LAB pochodzą z kalibracji 2024/25. Bez ponownego dopasowywania.
Rozliczenia wymagają zaakceptowanego wyniku i minimum 3 h od rozpoczęcia.
Korekty wyników są dopisywane jako nowe obserwacje; raport używa najnowszej.
Kopie wejść i skróty pomagają kontrolować zmiany. Historia commitów jest dowodem czasu publikacji; sam hash nie jest zewnętrznym znacznikiem czasu.
Brak prognozy nie jest liczony jako nietrafiony typ. Nie zmieniamy silnika produkcyjnego.
Wyniki nie mierzą ROI. Mała próba nie rozstrzyga przewagi modelu.

## Błędy pobierania


## Pominięte w bieżącym uruchomieniu


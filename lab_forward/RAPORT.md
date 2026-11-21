# RZOTKIEWKA — test przedmeczowy 2.1 / 2.2 LAB

Ostatnia obserwacja UTC: 2026-11-21T16:55:35.463322Z

Prognozy: 162–168 godzin przed meczem. Pierwszy zapis jest niezmienny.
Ten protokół różni się od retrospektywnego testu dokładnie 168 h przed meczem.

Zapisane pary prognoz: 45.

| Liga | Model | Rozliczone | Trafność | Brier ↓ | Log loss ↓ |
|---|---|---:|---:|---:|---:|
| Razem | v21 | 12 | 66.67% | 0.54971 | 0.93319 |
| Razem | v22_lab | 12 | 66.67% | 0.56196 | 0.95183 |
| bl1 | v21 | 1 | 0.00% | 1.19160 | 1.75843 |
| bl1 | v22_lab | 1 | 0.00% | 1.12442 | 1.67208 |
| bl2 | v21 | 5 | 60.00% | 0.56903 | 0.96737 |
| bl2 | v22_lab | 5 | 60.00% | 0.58748 | 0.99822 |
| bl3 | v21 | 6 | 83.33% | 0.42663 | 0.76717 |
| bl3 | v22_lab | 6 | 83.33% | 0.44696 | 0.79313 |

Wyłączone po zmianie terminu lub drużyn: 0.

Parametry LAB pochodzą z kalibracji 2024/25. Bez ponownego dopasowywania.
Rozliczenia wymagają zaakceptowanego wyniku i minimum 3 h od rozpoczęcia.
Korekty wyników są dopisywane jako nowe obserwacje; raport używa najnowszej.
Kopie wejść i skróty pomagają kontrolować zmiany. Historia commitów jest dowodem czasu publikacji; sam hash nie jest zewnętrznym znacznikiem czasu.
Brak prognozy nie jest liczony jako nietrafiony typ. Nie zmieniamy silnika produkcyjnego.
Wyniki nie mierzą ROI. Mała próba nie rozstrzyga przewagi modelu.

## Błędy pobierania


## Pominięte w bieżącym uruchomieniu


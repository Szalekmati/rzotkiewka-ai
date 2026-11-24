# RZOTKIEWKA — test przedmeczowy 2.1 / 2.2 LAB

Ostatnia obserwacja UTC: 2026-11-24T04:56:26.953754Z

Prognozy: 162–168 godzin przed meczem. Pierwszy zapis jest niezmienny.
Ten protokół różni się od retrospektywnego testu dokładnie 168 h przed meczem.

Zapisane pary prognoz: 56.

| Liga | Model | Rozliczone | Trafność | Brier ↓ | Log loss ↓ |
|---|---|---:|---:|---:|---:|
| Razem | v21 | 28 | 64.29% | 0.55638 | 0.93849 |
| Razem | v22_lab | 28 | 64.29% | 0.55887 | 0.94279 |
| bl1 | v21 | 9 | 55.56% | 0.57525 | 0.95694 |
| bl1 | v22_lab | 9 | 55.56% | 0.57786 | 0.96167 |
| bl2 | v21 | 9 | 55.56% | 0.61016 | 1.02051 |
| bl2 | v22_lab | 9 | 55.56% | 0.61575 | 1.02852 |
| bl3 | v21 | 10 | 80.00% | 0.49099 | 0.84807 |
| bl3 | v22_lab | 10 | 80.00% | 0.49059 | 0.84865 |

Wyłączone po zmianie terminu lub drużyn: 0.

Parametry LAB pochodzą z kalibracji 2024/25. Bez ponownego dopasowywania.
Rozliczenia wymagają zaakceptowanego wyniku i minimum 3 h od rozpoczęcia.
Korekty wyników są dopisywane jako nowe obserwacje; raport używa najnowszej.
Kopie wejść i skróty pomagają kontrolować zmiany. Historia commitów jest dowodem czasu publikacji; sam hash nie jest zewnętrznym znacznikiem czasu.
Brak prognozy nie jest liczony jako nietrafiony typ. Nie zmieniamy silnika produkcyjnego.
Wyniki nie mierzą ROI. Mała próba nie rozstrzyga przewagi modelu.

## Błędy pobierania


## Pominięte w bieżącym uruchomieniu


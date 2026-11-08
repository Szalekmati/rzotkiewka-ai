# 🫜 RZOTKIEWKA AI — audyt diagnostyczny 2.3

**Decyzja: NIE PODMIENIAĆ obecnego silnika ani strony.** To wyłącznie audyt offline na historycznym pliku testowym.

Plik: `mecze_test_22.csv`; 874 meczów w 102 dniach meczowych; zakres 2025-09-12T16:30:00Z — 2026-05-17T13:30:00Z.
Kontrola danych: **OK** (bez duplikatów; poprawne prawdopodobieństwa i pola kontrolne).

## Porównanie modeli na tym samym teście

| Model | Trafność 1X2 | Brier ↓ | Log loss ↓ | Śr. P(X) | Typy X |
|---|---:|---:|---:|---:|---:|
| 2.0 | 47.03% | 0.62499 | 1.03992 | 23.54% | 0 |
| 2.1 | 47.03% | 0.62566 | 1.04112 | 23.41% | 0 |
| 2.2 eksperyment | 47.03% | 0.62894 | 1.04516 | 26.43% | 0 |

**Rzeczywiste remisy:** 213/874 = 24.37%.
**Punkt odniesienia:** zawsze wybierając gospodarzy trafiono by 45.77%; model 2.1 ma przewagę +1.26 punktu procentowego na tych danych.
95% przedział bootstrap różnicy trafności 2.1 minus 'zawsze 1': [-2.22, +4.67] p.p. — nie traktować jako wykazanej przewagi.

## Co oznacza brak typów X?

Wybór 1/X/2 jest robiony przez **argmax** (największe z trzech prawdopodobieństw).
Model 2.1 przypisał remisowi średnio 23.41% przy 24.37% faktycznych remisów, ale P(X) nigdy nie była największa.
Najwyższe P(X) w 2.1: 34.38%; najmniejsza przewaga silniejszej prognozy 1/2 nad X: 4.49 p.p.
Zerowa liczba typów X **nie dowodzi błędu**. Prawdopodobieństwa należy oceniać oddzielnie od klasyfikacji; dodawanie sztucznego bonusu za remis bez walidacji może pogorszyć Brier.

## Kalibracja remisów — 5 grup o podobnej liczebności (model 2.1)

| Grupa (od najmniejszego P(X)) | Mecze | Średnie P(X) | Faktyczne remisy |
|---|---:|---:|---:|
| 1 | 174 | 19.80% | 25.86% |
| 2 | 175 | 22.21% | 22.29% |
| 3 | 175 | 23.47% | 21.14% |
| 4 | 175 | 24.67% | 27.43% |
| 5 | 175 | 26.87% | 25.14% |

## Wyniki ligowe

| Liga | Mecze | Brier 2.0 | Brier 2.1 | Brier 2.2 eksperyment | Trafność 2.1 |
|---|---:|---:|---:|---:|---:|
| bl1 | 264 | 0.61492 | 0.61514 | 0.62070 | 50.00% |
| bl2 | 270 | 0.64486 | 0.64547 | 0.64343 | 44.07% |
| bl3 | 340 | 0.61703 | 0.61809 | 0.62382 | 47.06% |

## Czy 2.0 jest naprawdę lepsza?

W teście Brier 2.0 jest mniejszy od 2.1 o **0.00066** oraz od eksperymentu 2.2 o **0.00394**.
Przedział bootstrap Brier(2.0) − Brier(2.1): [-0.00155, +0.00018].
Przedział bootstrap Brier(2.0) − Brier(2.2): [-0.00931, +0.00142].
Oba wyniki to drobne różnice retrospektywne, a nie potwierdzony wzrost jakości. **Nie promujemy żadnej nowej wersji na podstawie tego raportu.**

## Kolejność prac przed wydaniem 2.3 produkcyjnej

1. Zapisywać prognozy **przed meczem**, z datą utworzenia, datą spotkania, identyfikatorem modelu i danymi wejściowymi.
2. Rozdzielić ocenę prawdopodobieństw 1/X/2 od pokazywanego użytkownikowi typu.
3. Porównać kilka prostych, z góry ustalonych modeli na kolejnych nowych meczach, bez strojenia na teście.
4. Dopiero po uzyskaniu odpowiednich danych zbierać kursy z chwili prognozy i weryfikować opłacalność po uwzględnieniu kosztów.
5. Przygotować zbieranie opinii czterech testerów strony, bez deklarowania potwierdzonej skuteczności typerskiej.

**Ograniczenia:** audyt retrospektywny; brak niezależnego potwierdzenia archiwalności wejść do wcześniejszych prognoz, brak kursów i ROI. Wyniki nie dowodzą przewagi nad bukmacherem.

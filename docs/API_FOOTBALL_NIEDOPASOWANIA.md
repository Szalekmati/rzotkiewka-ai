# RZOTKIEWKA – analiza niedopasowanych meczow, bez zgadywania

Pierwsze porownanie OpenFootball i API-FOOTBALL:
[GitHub Actions](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43060940735).
Wczesniej: 43 mecze na zrodlo, dopasowane 13, 13 zgodnych wynikow,
30 niedopasowanych w kazdym zrodle.

Nowy audyt sprawdza, **dlaczego algorytm nie potrafil polaczyc rekordow**,
a nie zaklada bledow dostawcy. Kategorie dla kazdego niezidentyfikowanego
rekordu sa rozlaczne i sumuja sie do calkowitej liczby rekordow:

- `pair_other_date`: dokladnie te same znormalizowane nazwy pary
  gospodarze–goscie pojawiaja sie w drugim zrodle, ale poza +/- 1 dniem.
- `both_names_exist`: oba identyfikatory nazw wystepuja w przeciwnym
  zrodle w tej samej roli (dom/wyjazd), lecz nie ma tej pary.
- `only_home_name` / `only_away_name`: tylko jedna nazwa pasuje.
- `neither_name`: brak tych znormalizowanych nazw w odpowiednich rolach.

To **tylko diagnostyka**. Brak nazwy nie potwierdza rozbieznosci wyniku
ani tego, czy to ten sam klub: mozliwe aliasy, inne sklady lig, zmiany
terminow, ograniczenia zbioru historycznego. Nie dopasowujemy klubow na
podstawie podobienstwa wyniku (w ten sposob mozna zawyzyc zgodnosc).

Program nie loguje indywidualnych meczow ani nazw z prywatnej odpowiedzi
API i nie zapisuje danych dostawcy. Ręczne uruchomienie = co najwyzej
2 zapytania `/fixtures` w ramach juz oplaconego planu (proba z sierpnia
2026). PR/push uruchamiaja tylko testy offline. Bez zmian `predictions.json`,
`lab_forward/`, modelu i publicznej strony.

Nastepny krok po raporcie: zaplanowanie recznej weryfikacji konkretnych
aliasow i niezaleznej kontrolnej probki z zaufanego aktualnego zrodla,
bez automatycznego zatwierdzania meczow.

## Wyniki faktycznego uruchomienia, 11.11.2026 (17:01 UTC)

[GitHub Actions — jednorazowa diagnoza](https://github.com/Szalekmati/rzotkiewka-ai/actions/runs/43064068889).

Badano okres 21–31.08.2026. Obie ligi w API i OpenFootball mialy po
20 (Premier League) oraz po 23 (LaLiga) rekordy. Bazowe dopasowanie
pozostalo niezmienione: 9 i 4 mecze, wszystkie 13 zgodnych co do wyniku.

| Kryterium | Premier League | LaLiga |
|---|---:|---:|
| Dopasowane pary | 9 | 4 |
| Niedopasowane pary w kazdym zrodle | 11 | 19 |
| Unikatowe znormalizowane nazwy druzyn na zrodlo | 20 | 20 |
| Wspolne znormalizowane nazwy druzyn | 14 | 9 |
| Ta sama para z roznica dat ponad 1 dzien | 0 | 0 |
| Obie nazwy istnieja w odpowiednich rolach, inna para | 0 | 0 |
| Tylko nazwa gospodarzy obecna | 5 | 7 |
| Tylko nazwa gosci obecna | 5 | 7 |
| Zadna z obu nazw nieobecna w drugim zrodle | 1 | 5 |
| Niejasne dopasowania | 0 | 0 |

Kategoriom po stronie API odpowiadaja w tej probie identyczne liczniki
jak po stronie OpenFootball. 9/9 testow offline przeszlo. W ramach
posiadanego planu PRO wykonano **2 zapytania /fixtures** i odczyt statusu.

**Interpretacja:** dominujacym problemem jest brak dokladnej zgodnosci
identyfikacji par nazw. Nie jest potwierdzone, czy wynika to tylko z
aliasow nazw druzyn, odmiennych skladow lig, roznych spotkan czy bledu
ktoregos zrodla. Nie wolno laczyc klubow wedlug podobienstwa wyniku
ani uznawac niedopasowanych za falszywe dane.

**Kolejny krok:** sprawdzic recznie i na niezaleznym wiarygodnym zrodle
tozsamosc druzyn oraz zgodnosc skladów lig i terminarzy 2026/27.
Nastepnie utworzyc jawna, zweryfikowana mape ID/aliasow z pochodzeniem
i wersja, przetestowac ja offline i dopiero wtedy ponowic porownanie
z kontrola przeciekow danych. Nie promowac lig do produkcji bez tego.

Jednorazowy workflow usunieto. Nadal brak zmian w modelu, LAB, stronie,
`predictions.json` i platnosciach.

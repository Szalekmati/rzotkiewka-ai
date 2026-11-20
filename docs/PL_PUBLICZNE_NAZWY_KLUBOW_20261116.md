# Premier League 2026/27 — przegląd publicznych nazw klubów (16.11.2026)

**Status:** `RESEARCH_ONLY` / `ID_NOT_VERIFIED`. To porównanie **publicznych nazw** OpenFootball i oficjalnej Premier League, **nie** lista sześciu mapowań z dostawcą API-Football i **nie** pozwolenie na produkcję.

## Reprodukowalne źródła

1. Oficjalny skład 20 drużyn Premier League 2026/27: https://www.premierleague.com/en/news/4365156
2. Przypięty historyczny stan publicznego archiwum OpenFootball 2026/27: https://github.com/openfootball/england/blob/9ee7a0c351805c99cc334478a9bf04b7d0432fec/2026-27/1-premierleague.txt
3. Rejestr oficjalnych nazw w projekcie: `api_football_official_roster.py`, `OFFICIAL[39]["clubs"]`.
4. Stan zatwierdzeń ID w projekcie: `data/identity_release_registry.json`.

Weryfikacja: odczytano unikatowe nazwy drużyn z rekordów meczowych publicznego pliku (bez przepisywania meczów/wyników); porównano z listą `OFFICIAL[39]` z oficjalnego źródła. Normalizacja: Unicode NFKD i usunięcie znaków diakrytycznych, małe litery, `&` → `and`, usunięcie skrajnych przyrostków/przedrostków `FC`, `CF`, `AFC` i spacji. Dopasowanie jest **dokładne po normalizacji**, jednoznaczne 1:1; żadne podobieństwo rozmyte, wyniki meczów, kursy czy daty nie służyły do rozpoznawania klubu.

## Wynik

- Nazwy z publicznego archiwum OpenFootball: **20 unikatowych**.
- Kluby na oficjalnym wykazie: **20 unikatowych**.
- Dopasowane po normalizacji: **20/20**.
- Brakujące, nadmiarowe i kolizyjne nazwy: **0**.
- Kandydatów aliasów **OpenFootball ↔ API-Football** według wcześniejszego rejestru: **6**, lecz nie da się z tego badania ich indywidualnie wskazać ani zatwierdzić bez dostawcy.
- Niezależnie sprawdzone `provider_team_id` dla Premier League w rejestrze: **0/6**.

| Wariant publiczny OpenFootball | Oficjalna nazwa Premier League |
| --- | --- |
| AFC Bournemouth | AFC Bournemouth |
| Arsenal FC | Arsenal |
| Aston Villa FC | Aston Villa |
| Brentford FC | Brentford |
| Brighton & Hove Albion FC | Brighton & Hove Albion |
| Chelsea FC | Chelsea |
| Coventry City FC | Coventry City |
| Crystal Palace FC | Crystal Palace |
| Everton FC | Everton |
| Fulham FC | Fulham |
| Hull City AFC | Hull City |
| Ipswich Town FC | Ipswich Town |
| Leeds United FC | Leeds United |
| Liverpool FC | Liverpool |
| Manchester City FC | Manchester City |
| Manchester United FC | Manchester United |
| Newcastle United FC | Newcastle United |
| Nottingham Forest FC | Nottingham Forest |
| Sunderland AFC | Sunderland |
| Tottenham Hotspur FC | Tottenham Hotspur |

## Bramki przed dalszym użyciem

- Wskazać dokładnie sześć **rzeczywistych** kandydatur aliasów z wewnętrznego audytu API (bez ich zgadywania na podstawie powyższej tabeli).
- Osobno potwierdzić każdy `provider_team_id` oraz klub i sezon przez wiarygodne niezależne źródło na stronie konkretnego klubu, a nie ogólnej listy; zweryfikować treść, nie tylko format URL. Nie kopiować surowych komercyjnych rekordów API do publicznego repo.
- Dopiero po uzyskaniu kompletnych map, kontroli licencji, jakości meczów i prospektywnego testu modelu rozważać nową ligę.

**Nie zmieniono `reviewed_identity_links`, `release.requested`, produkcji, LAB, Pages ani opłat.**

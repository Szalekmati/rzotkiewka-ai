# RZOTKIEWKA AI — rozdzielenie deklaracji ID od potwierdzenia (16.11.2026)

Status: **DRAFT / RESEARCH_ONLY / STOP**. Ta gałąź bazuje na PR #49 (który zależy od PR #48). Nie jest wdrożona do main.

## Dlaczego
Zielone testy struktury rejestru nie dowodzą, że link naprawdę identyfikuje numer team ID nadawany przez API-Football. Sam link HTTPS i tekst „reviewed_by” można podać bez jakiegokolwiek odczytu treści. Oficjalne listy klubów potwierdzają nazwy, a nie numery wewnętrzne dostawcy.

## Nowy sposób raportowania
- `submitted_identity_link_entries`: liczba syntaktycznie poprawnych deklaracji z wymaganymi metadanymi.
- `independently_verified_id_links`: **0** w bramce offline — nie wykonuje ona kontroli stron ani treści API.
- `production_release_allowed`: zawsze **false**. Wniosek o wydanie jest odrzucany, również po dostarczeniu 17/17 samych deklaracji.

## Procedura przyszłej niezależnej weryfikacji (niezrealizowana)
1. Pozyskać autentyczny identyfikator, nazwę, ligę i sezon z dostawcy do kontrolowanego, niepublicznego pakietu dowodowego, bez kluczy ani surowego feedu w publicznym repo.
2. Zestawić je z niezależnym źródłem konkretnych spotkań lub nazw klubów (oficjalna lista uczestników sama nie potwierdza provider ID).
3. Zarejestrować konkretną datę, źródło, osobę sprawdzającą, status i odrębną decyzję właściciela; nie nadawać automatycznie statusu VERIFIED.
4. Zweryfikować osobno prawa do danych oraz prospektywne testy modelu. Dopiero potem można projektować ręczną bramkę wydania.

## Regresja
Dodany test potwierdza, że **17/17** syntaktycznie poprawnych, lecz niezweryfikowanych wpisów i pozytywne deklaracje innych zgód nadal kończą się STOP.

Bez nowego crona, pobierania API, zmiany LAB, Pages, prognoz, Premium ani opłat. Brak automatycznego merge.

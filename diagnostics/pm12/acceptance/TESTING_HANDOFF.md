# Przekazanie wątku pomiarowego PM12 — 19 listopada 2026

## Cel i podział odpowiedzialności

Nowy wątek prowadzi pomiary fizyczne kolejnych płyt i zapisuje kompletną,
identyfikowalną dokumentację maszynową. Osobny wątek raportowy pracuje offline:
korzysta z tych samych dekoderów, analiz i eksportera, generuje rysunki oraz LaTeX/PDF.
Raportowanie nie może wymagać ponownego podłączenia mierzonej płyty.

Repo: `/home/codex-hil/fit-testing-publish`, remote `publish`:
https://github.com/codex-hil/FIT_testing_sw , branch `pm12-integrator-scan-20261113`.
Najpierw przeczytaj `PRODUCTION_WORKFLOW.md`, potem ten dokument.
`REPORTING_HANDOFF.md` opisuje zamknięty pakiet pierwszej płyty, nie konfigurację
nowego DUT. Stosuj bieżące AGENTS.md i rezerwacje sprzętu.

## Stan odziedziczony — sprawdź przed użyciem

Ostatnio potwierdzona płyta: **PM12-K7-3A17A1B402212223**, EEPROM MCU1803.
Ostatnia deklaracja: symulatory3–6, oba USB na6. Slot7 porty RJ45
0/1/2/3→PM6/5/4/3; odpowiadające pary rejestratora8/9,10/11,12/13,14/15.
Nie traktuj tego jako aktualnego podłączenia bez sprawdzenia. Właściciel może już
przepiąć płytę lub symulatory. Numery kanałów PM w dokumentacji są1..12.

Ostatni wsad FPGA `ff2f746c` zawiera IPbus, bufory ADC/TDC i diagnostykę łącza.
Obraz SRAM i SHA256 są podane w `PRODUCTION_WORKFLOW.md` oraz w zamkniętym pakiecie.
CPLD/MCU wymagają zgodnego wsadu testowego — nowa płyta nie musi go mieć.
Testy nie programują ich automatycznie. Rejestracja DNA działa przed uruchomieniem
IPbus, ale samo rozpoczęcie sesji wymaga sprawnego stanowiska i oczekiwanego obrazu.

PM12 komunikuje się przez Kasli jako translator niestandardowej szybkości łącza:
ostatnio SFP1 Kasli↔PM12, SFP0 Ethernet; nie przełączaj zegarów na podstawie
założenia, że jest to zwykłe bezpośrednie1000BASE-X PM↔switch.
Wspólne odniesienie LHC:40.0787MHz do PM, jego trzykrotność do Kasli.
Nie zmieniaj CDCE/PLL/Silabs ani globalnie nie zwalniaj wyjść Kasli.
Slot6 HDMI/SPI ma pozostać sterowany; obsługa timingowa dotyczy slot7.

## Katalogi i tożsamość

Duże dane zapisuj na zamontowanym NVMe:

```
/srv/codex-hil-nvme/pm12-board-registry.json
/srv/codex-hil-nvme/pm12-board-sessions/BOARD_UID/UTC-unikalna-sesja/
  station.json               # niezmienny snapshot faktycznego podłączenia
  session.json               # identyfikacja i lista pomiarów
  identity/                  # surowe potwierdzenia tożsamości
  measurements/UNIKALNY_POMIAR/
    measurement.json         # przebieg wykonania, nie automatyczne PASS
    files.sha256.json
    native/                  # surowe bufory i wyniki adaptera, jeśli dotyczy
```

Nazwy wewnątrz pomiaru zależą od adaptera; np. batch timing ma `tdc/`,
`discovery/` i `phase-chNN/`. Nie zmieniaj struktury po zamknięciu pomiaru.
Każde przepięcie USB lub zmiana obsady wymaga nowej konfiguracji i nowej sesji,
również na tej samej płycie. Nie edytuj `station.json` istniejącej sesji.

UID pochodzi z DNA FPGA. S/N MCU, adres IP, numer kabla i `active.json` są tylko
pomocnicze. Sesja sprawdza DNA/MCU/PGOOD/obraz oraz wiąże JTAG z Ethernetem
wyzwaniem licznikowym i UART z tym samym FPGA przez test scratch+restore.
Nie omijaj niezgodności i nie dopisuj nowego UID do starego wyniku.

## Początek pracy

Polecenia wykonuj z katalogu repo; placeholdery zastąp rzeczywistymi ścieżkami
z odpowiedzi narzędzi. Nie wklejaj wszystkich komend jako niepilnowanego batcha.

```sh
cd /home/codex-hil/fit-testing-publish
PY=/home/codex-hil/kasli-diot-bringup/.venv/bin/python
A=diagnostics/pm12/acceptance
ROOT=/srv/codex-hil-nvme/pm12-board-sessions
$PY $A/board_session.py enroll \
  --station $A/profiles/optiplex-session.example.json --root "$ROOT" \
  --registry /srv/codex-hil-nvme/pm12-board-registry.json
```

Szablon jest nieprzypisany do płyty. Enrollment czyści odziedziczone deklaracje
połączeń. Uzupełnij zwrócony plik konfiguracji: rzeczywiste `fitted_channels`,
`stimulated_channel`, mapowanie par DAC oraz flagi wejścia ADC/integratora.
Zapisz deklarację operatora i zdjęcia, jeśli dostępne; nie wymyślaj numerów testerów.
Dla SMU wymagane są jawne host/serial, `shared_monitors_connected=true`,
`smu_sense="local-force-0A"`. Force HI/LO oznacza pomiar lokalny2-wire;
Sense HI/LO wymaga osobno zweryfikowanej konfiguracji. Nie zgaduj podłączenia.

Gdy potrzebne jest przygotowanie FPGA/CPLD/MCU, wydziel etap setupu i zachowaj
wersje, hashe, identyfikację oraz odczyt po programowaniu. Dostępny loader SRAM
jest opisany w workflow; nie oznacza to gotowego automatycznego provisioningu
nowej płyty. Ciężkie buildy tylko na Dellu, JTAG/UART lokalnie pod rezerwacjami.

```sh
$PY $A/board_session.py begin --station ENROLLED_CONFIG --root "$ROOT"
```

Zwróconą ścieżkę zapisz jako SESSION. Musi mieć status READY.

## Kolejność i wejścia do procedur

| Etap | Wspólne narzędzie | Warunek / istotne ograniczenie |
|---|---|---|
| Identyfikacja i zgodność endpointów | `board_session.py enroll`, `begin` | Każda nowa płyta; DNA jest UID |
| JTAG / boundary scan | istniejące `boundary.py`, `suite.py`, źródła testów połączeń | Osobna procedura ingerująca w piny; nie uruchamiaj przez kopiowanie starej kampanii; sprawdź zgodność netlisty, obsady, wsadów i stan przywrócenia |
| MCU, I2C, transport ADC, HDMI, zegary | `board_check.py --session SESSION --repeats 12` | Sprawne IPbus, konsola i zgodny obraz; powtórz na końcu |
| Monitory napięć symulatorów | `fixture_batch.py --session SESSION --kind monitors` | Cztery zadeklarowane symulatory, wspólne wyjście do SMU; tylko jeden mux aktywny |
| Wewnętrzne DAC B/C/D | `fixture_batch.py --session SESSION --kind dacs` | SMU0A/Force i sprawdzony ID; DAC-A bada osobno faza |
| TDC i faza | `fixture_batch.py --session SESSION --kind timing --phase-intervals 100 --settle 1` | Discovery rzeczywistej mapy RJ45, quiet/count/crosstalk, potem skany fazy |
| Sama faza | `fixture_batch.py --session SESSION --kind phase --phase-intervals 100 --settle 1` | Ponowne discovery; zachować niezawodny1s settling |
| ADC A/B, charakterystyka i linie | `board_session.py measure --session SESSION --kind adc --channel N --phase-code CODE --sample-window WINDOW --points 257` | USB DAC0/1→ADC, DAC2/3 zaparkowane; rzeczywista trasa w konfiguracji |
| Integrator A/B | `board_session.py measure --session SESSION --kind integrator --channel N --phase-code CODE --sample-window WINDOW --pairs P:N P:N ...` | USB DAC2/3→integrator; jawne pary napięć, baza1.024/2.048V |
| Weryfikacja zapisów | `board_session.py verify --session SESSION` | Offline, integralność nie jest akceptacją montażu |

Uruchamiaj skrypty acceptance przez `$PY $A/NAZWA.py ...`.
Na pojedynczym podłączeniu USB najpierw ADC, potem integrator; monitory i timing
można wykonać dla całej czwórki bez przepinania analogowego USB. Po deklaracji
przepięcia zakładaj nową sesję i wykonuj kolejny kanał. Obsada typowo1–4,5–8,9–12,
ale przyjmuj rzeczywiste kanały podane przez operatora, nie domyślną kolejność.

### ADC i integratory — zachować znaczenie pomiaru

Nie przekraczać3.3V na wejściach, mimo możliwości DAC do5V. Nie uruchamiaj obu
tras analogowych naraz, jeśli nie wynika to z konkretnej zweryfikowanej procedury.
Faza i okno próbkowania są parametrami metody, nie kosmetyką wykresu.
`before-str`/0 to punkt startowy; na pierwszej płycie ADC2 wymagał `str-rise`/32768.
Przed pełnym skanem sprawdź stabilne dane w odpowiednim oknie. Niestabilność bitów,
STR, tagów, generacji czy nasycenie zachowaj jako błąd, nie uśredniaj jej do PASS.

Dla integratora stałe pobudzenie podczas resetu daje niezerowe poziomy; nie
utożsamiaj wszystkich próbek z jednym idealnym zerem. A/B mają różne biasy.
Wyznacz bracket, następnie zagęść krok pojedynczej gałęzi do100µV wokół równowagi;
zamroź model i wykonaj niezależne powroty oraz kontrole±5mV. Nie szukaj równowagi
krokiem wielokrotnie większym niż jej zakres. Parametry i faktyczne napięcia zapisz.
`analyze_reset_reference.py` w `cfd_simulator/` korzysta z coarse/fine/validation,
sprawdza wspólny UID i fazę; wymagania jego modelu trzeba spełnić danymi, a nie
zmieniać progi po obejrzeniu wyniku. To diagnostyczna metoda funkcjonalna, nie
kalibrowany pomiar prądu zerowego ani automatycznie metoda dla każdego przypadku.

Normalna praca integratorów20MHz, ADC80MHz. Testy nie przeprogramowują CPLD;
wsad2MHz i wymuszony reset są osobnymi eksperymentami diagnostycznymi.

## Jeden kontrakt danych dla pomiarów i raportu

Istnieją już wspólne narzędzia akwizycji, walidacji i `dossier.py`.
**Nie istnieje jeszcze kompletny jeden runner od przygotowania nowej płyty,
przez wszystkie analizy, po automatyczny dobór89receipts.** Nie przedstawiaj go
jako gotowego. W pierwszym pakiecie część receipts była normalizowana podczas
konsolidacji. Ich jawny przykład jest w
`evidence-production-data-20261119/selection.json`; dotyczy wyłącznie starego UID.

Jeżeli potrzebna jest dalsza normalizacja, dodaj ją do repo jako wspólne,
offline narzędzie z testami na rzeczywistych formatach adapterów. Nie twórz
jednorazowego konwertera poza repo ani osobnej interpretacji liczb w LaTeX-u.
Raport musi importować te same analizy i nie może liczyć innego wyniku akceptacji.

Docelowe receipt wybranego przypadku zachowuje:

- `board_uid`, `channel` (null dla board), `status`, nazwę i wersję metody;
- czas, konfigurację/clock epoch, bank, fazę DAC i okno dekodera;
- wyniki z jednostkami i kryteria, surowe pliki, ich hashe, wersje źródeł;
- `source_files` jako względne ścieżki do istniejących danych, ewentualne
  `original_summary`; żadnych samotnych wyników JSON bez surowych źródeł;
- `curves` z `name`, `bank`, `x_unit`, `y_unit`, jednakowej długości `x`/`y`,
  jeśli mają wejść do wspólnego `series.csv`.

`COMPLETE` oznacza wykonanie akwizycji. PASS wymaga analizy i jawnych kryteriów;
PASS_FUNCTIONAL oznacza oddzielnie opisaną metodę funkcjonalną. ERROR/INCOMPLETE
pozostają w sesji. Powtórka tworzy nowy zapis z powodem; selekcja wskazuje konkretny
wynik, bez nadpisywania poprzedniego. Nie przyjmuj „najnowszego pliku” jako selekcji.

Dla pełnego zakresu pierwszej płyty macierz ma89pól: board jtag/mcu/i2c/hdmi/ethernet
oraz7×12: cfd-monitor/cfd-dacs/gate-phase/tdc/adc-dc/adc-lines/integrator.
To wzorzec pokrycia, nie automatyczne przeniesienie PASS na następną płytę.
Testy prądów/sensorów zawierają się w checks board, a nie w pomiarach CFD DAC.
Nie deklaruj testu wszystkich relay/netów, ochrony PG, absolutnego jitteru,
kalibracji lub BER, jeśli faktyczna procedura tego nie mierzy.

## Zamknięcie partii i przekazanie reporterowi

Po każdej czwórce opublikuj krótką macierz wykonane/brak/błąd, sesje i faktyczne
podłączenie. Eksport częściowy ma jawnie niepełny zakres i listę braków; nie
zmniejszaj po cichu wymaganej macierzy pełnej płyty, żeby dostać kompletność.

Po całej płycie przygotuj `EXPLICIT_SELECTION.json`: UID, zakres, required_cases,
selections, metadata omissions i scope exclusions. Każda selection wskazuje
`case`, `test`, `channel`, `status`, `method`, `basis`, `measured_utc`, katalog
`source` i względny `receipt`. Wybór musi być odtwarzalny, również dla powtórek.

```sh
python3 $A/board_session.py verify --session SESSION
python3 $A/dossier.py build --selection EXPLICIT_SELECTION.json --out NEW_DOSSIER
python3 $A/dossier.py verify --root NEW_DOSSIER
python3 $A/dossier.py export --root NEW_DOSSIER --out NEW_REPORT_INPUTS
```

Raporter dostaje dossier z blobs/release.json i eksport:
`measurements.json`, `coverage.csv`, `series.csv`; również konfiguracje, identyfikację,
stan końcowy, wersję repo, opis setupu, zdjęcia/numery albo jawne braki metadanych.
Archiwum musi mieć SHA256 i manifest, kopia SMB być sprawdzona odczytem po zapisie.
Nazwa zawiera nowy UID i wersję release; nie nadpisuj pakietu pierwszej płyty.
Do Git trafiają skrypty, procedury i kompaktowy indeks; duże bufory na NVMe/SMB.

Kryterium zakończenia wątku: żaden wybrany wynik nie wymaga pamięci rozmowy,
żaden pomiar nie miesza UID, wszystkie źródła istnieją i są zahashowane,
braki/błędy są jawne, raport daje się zbudować offline z przekazanego pakietu.

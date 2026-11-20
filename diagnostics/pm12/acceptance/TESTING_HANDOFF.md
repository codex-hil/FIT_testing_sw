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

## Aktualizacja20listopada2026 — start od drugiej płyty

### Kontynuacja20listopada2026 — identyfikacja i boundary drugiej płyty

Aktualny DUT ma DNA **2A17A1B40221242B**, UID **PM12-K7-2A17A1B40221242B**.
Operator poprawił podłączenie do właściwego z dwóch złączy JTAG. Kabel
210249A73E43 następnie odczytał12×XC2C128+XC7K160T. EEPROM1803 pozostaje
celowo powielony; nie stosować go jako UID. Operator zadeklarował CFD1–4 i oba
analogowe USB na kanale1. Mapy timingowej nie odkrywano, SMU niepotwierdzony.

Dwa pomiary znanej diagnostyki c9fbd027 dały168/168 połączeń w obu ścieżkach,
ale błąd freeze. Stary HDL taktował komendy USER2 sygnałem TCK z USER1.
Symulacja z nieruchomym TCK USER1 odtworzyła błąd starego HDL i potwierdziła
poprawkę z osobnym TCK/RESET/CAPTURE USER2 oraz blokadą starego UPDATE.
Nowy obraz zbudowano na Dellu, zachowując starsze źródła i artefakty. SHA256:
`091501ff3cb1b33a2a38f1d970f0edbdc3e6915101920973add51737f33bc62d`.
Trzecia akwizycja przeszła oba338-wektorowe tory168/168, wszystkie3cykle
run/freeze/resume/reset i reset TAP. To **PASS natywnego testu**.

Cały identity-bound wrapper pozostaje **ERROR**: przywrócono SRAM ff2f746c
z poprawną sygnaturą JTAG, ale kontrola końcowa IPbus miała timeout. Jeden
jawny reset PHY PM na Kasli nie zmienił profilu zegarów/DIO/HDMI. Późniejszy
probe odebrał komplet rejestrów ff2f746c, lecz kolejne `begin` znowu miało timeout.
Sporadyczne odpowiedzi192.168.2.240 **nie zostały powiązane z DNA nowego DUT**;
nie uznawać ich za PASS Ethernetu. Sprawdź, że tylko jeden DUT jest w torze
statycznego IP, faktyczny SFP i odniesienie. Nie zmieniaj automatycznie PLL.
Testy ADC/integratorów/timingu zatrzymano przed pobudzeniem, bo sesja nie ma READY.
MCU/CPLD/Flash nie programowano ponownie, konfiguracji zegarów nie zmieniano.

Wspólny `boundary.py` jest poprawiony: zaczyna od fizycznego DNA bez wymogu
IPbus, używa niezmienionych wektorów `test_board.py`, zachowuje surowe logi,
sprawdza tożsamość przed przywracaniem i korzysta z aktualnego loadera SRAM.
`test_board.controls` odtwarza kryteria freeze/resume/reset z surowych raportów.
`station_config.py`, `build_diagnostic.py`, `station_probe.py`,
`jtag_transport_probe.py`, `link_recovery.py`, `boundary_release.py`,
`package_release.py` i `publish_release.py` są wspólnymi narzędziami w repo.
Szablon wskazuje nową sprawdzoną diagnostykę i aktualny obraz przywracania.
Procedura pozostaje w PRODUCTION_WORKFLOW.md.

Indeks: `evidence-board2-boundary-20261120/index.json`. Dane i pakiet:
`/srv/codex-hil-nvme/pm12-board-sessions/PM12-K7-2A17A1B40221242B/`.
Release `releases/20261120-boundary-v1/` zawiera dossier i eksport89pól:
**1ERROR,88NOT_RUN**, REVIEW. Native PASS jest zachowany jako podwynik;
nie przenosić go na wynik całej procedury. Manifest/archiwum mają SHA256,
odczyt offline sprawdzony. SMB:
`\\192.168.2.6\codex-hil\ALICE\PM12-test-reports\PM12-K7-2A17A1B40221242B\board2-boundary-20261120-v1`.
Kopia SMB zweryfikowana odczytem; poprzedniej płyty/pakietu nie nadpisano.

W danych próby zegara zachowano błędne pole pochodne zakładające125MHz sys.
Wspólna analiza `station_probe.analyze_record` jawnie je unieważnia i liczy
niekalibrowane obserwacje tylko z surowych liczników/czasu hosta. Poprawna
normalizacja jest w `boundary-evidence/related-analyses/`; nie importuj starego pola.

### Stan wejściowy sprzed powyższych pomiarów (zachowany historycznie)

Użytkownik przenosi dalszy bring-up do nowego wątku. W tym wątku nie wykonano
boundary scan nowej płyty; wykonano wyłącznie preflight odczytu DNA/łańcucha.
Ostatni wynik: kabel Digilent210249A73E43 jest widoczny, ale zgłasza **No devices
detected**. Sprawdź rzeczywiste podłączenie JTAG nowej płyty i właściwy kabel pod
rezerwacją; nie próbuj programować innych widocznych Digilentów na chybił trafił.
Łańcuch oczekiwany przez test:12×XC2C128(ID16d8a093)+Kintex7(ID0364c093).
DNA nowej płyty nadal PENDING; nie wolno przypisać jej starego UID.

MCU nowej płyty miał pusty FLASH/boot i fabryczne fusebity. Zainstalowano
ostatnią aplikację diagnostyczną z `FIT_PM_FW_uPC/development/build/development.bin`,
pełny obraz źródłowy SHA256
`f49643c80c6189afebdaa3f7301f4ecebacb55645e60456f66831106d38b9464`.
Zapisano tylko application128KiB, niezależny odczyt zgodny. Boot pozostaje pusty.
Na wyraźne polecenie użytkownika skopiowano EEPROM pierwszej płyty:
**S/N1803 jest teraz celowo powielony i nie identyfikuje DUT**.
MCU production-signature SHA256 nowego egzemplarza:
`f1b955294628e001d491e6117e1ae48886342fed01f4536b8dd731f2b083c11c`.
Fuse0/1/2/4/5=FF/00/FE/F3/E8, niezależnie odczytane; JTAG MCU wyłączony.
Stary AVRDUDE błędnie potwierdzał standardowy zapis fuse4, zostawiającFE;
sprawdzony alias i logi są w `../mcu/evidence-board2-20261120/`.
Nie powtarzaj programowania w ciemno; jest już zakończone.

Użytkownik zalutował zworki magistrali czujników. I2C LINES07, OWNER00,
wszystkie trzy INA3221 odpowiadają CONFIG7127, muxy po odczycie00/00.
Trzy kolejne próby dały te same napięcia: LDO1.000/1.200/1.808V,
P3V8=3.904V,P3V3=3.328V,P1V8=1.784V,P1V0=1.008V,P5V5=5.496V.
Temperatura31.25C, PGOOD stabilny, konsola i PLL działają. Nie jest to jeszcze
kwalifikacja napięć pod obciążeniem FPGA. Obsada symulatorów/USB na tej nowej
płycie nie została zadeklarowana; nie przenoś deklaracji z pierwszej płyty.

Dowody w repo:
- `../mcu/evidence-board2-20261120/`: programowanie i odczyty kontrolne;
- `../mcu/evidence-board2-sensors-20261120/`: surowe odczyty, CSV, źródło akwizycji;
- `evidence-board2-jtag-preflight-20261120/`: nieudany odczyt JTAG, bez EXTEST
  i bez jakiegokolwiek programowania FPGA/CPLD.

Pełne lokalne materiały: `/srv/codex-hil-nvme/pm12-board2-mcu-20261120/`.
`pm12-campaigns/active.json` wskazuje nową płytę jako niepowiązaną (UID null).
Dane pierwszej płyty pozostają zamknięte. Wszystkie zadania sprzętowe tego wątku
zakończone, rezerwacje zwolnione; nie pozostawiono procesu pomiarowego.

### Następny test: istniejący skrypt boundary scan

Wspólny skrypt to `diagnostics/pm12/test_board.py`, wersjonowany w tym repo,
a nie jednorazowy plik z katalogu artifacts. Sprawdza168połączeń data/STR,
338wektorów walking-one/walking-zero, niezależny odczyt komórek boundary FPGA,
porównanie z `pinmap.json` i sterowanie reset/freeze/resume diagnostyki.
Zapisuje surowe logi, `report.json`, `connections.csv`, hashe schematu/bitstreamu.
CPLD EXTEST jest chwilowy; nie ma zapisu firmware CPLD ani konfiguracji FLASH.
To nie jest test wszystkich netów płyty ani całego toru analogowego.

Po odzyskaniu łańcucha najpierw odczytaj DNA i przypisz nowy UID. Sprawdź zgodność
obsady i schematu z mapą oraz hash obrazu testowego. Znany obraz diagnostyczny:
`/home/codex-hil/fit-bringup/gateware/pm12_link_diag/build/pm12_link_diag.bit`,
SHA256 `c9fbd02768ce12750dc68b8bb24c34403027a65f9e002661e29bb3d2e2df7a1a`.
Programowanie FPGA SRAM jest częścią tego testu; stary obraz SRAM zostanie utracony.
Natywny `test_board.py` przywraca TAP/CPLD do trybu funkcjonalnego, ale **pozostawia
w FPGA diagnostykę**, nie przywraca IPbus. Ustal jawnie obraz końcowy, sprawdź jego
hash i przywróć go kontrolowanym loaderem; sprawdź stan końcowy także po błędzie.

Nie uruchamiaj bez poprawek `acceptance/boundary.py`: jego przywracanie wymaga
starego c7c42d28 i wywołuje wyłączony `station.integrated`; szablon ma też historyczną
ścieżkę restore. Nowy wątek ma opakować istniejący `test_board.py` w sprawdzanie
DNA/rezerwacje/konfigurację oraz bezpieczne, jawne zakończenie zgodne z aktualnym
wsadem, zachowując jeden skrypt testowy dla następnych płyt i reporterów.
Wyniku nie wpisuj jako PASS, dopóki pełne wektory i kontrola zakończenia nie przejdą.

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

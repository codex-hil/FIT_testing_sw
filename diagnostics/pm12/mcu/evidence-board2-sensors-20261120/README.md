# Board2 sensor reads after jumper soldering —20 November2026

Owner soldered sensor jumpers. SDA/SCL/RESET now all high (LINES07), ownership00.
All three INA3221 respond, CONFIG7127, restored mux masks00/00. Three repeated
reads per sensor give identical voltages at displayed8mV resolution. ADC/FPGA
not configured; these readings represent this powered setup, not loaded-operation
qualification. PGOOD checked before each read. Temperature ADT7311 ID C3,
raw0FA0 =31.25degC. No firmware, EEPROM, fuse, PLL or FPGA changes in this test.

Raw replies, PGOOD snapshots and executed acquisition source are retained here.
voltages.csv independently checks signed bus codes at8mV/LSB. Route6/channel3
is the known unpopulated diagnostic input, not a measured supply rail.
P3V8 current is not qualified on this new board: installed shunt status is not
confirmed; firmware's historical R15 label is preserved in raw data.

Record is staged under board2, MCU prodsig hash in raw receipt. FPGA DNA remains
pending; copied EEPROM serial1803 must not link it to the old board UID. These
records supersede the earlier BUS_STUCK attempt for communication status only;
that failed attempt remains preserved. Raw NVMe directory is recorded in the
acquisition file and measurement timestamp. Further enrollment waits for DNA.

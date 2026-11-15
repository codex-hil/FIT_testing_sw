# MISO drive 12 -> 4 -> 12 mA, 2026-11-15

Board PM12-K7-3A17A1B402212223, MCU serial 1803.
Matched normal SPI divider 601/read 0 produced SYS resets at 12 mA (6/6),
4 mA (12/12), and 12 mA again (12/12). No incorrect SPI replies.
Additional 4 mA reads 0/1 reset in 12/12 cases; read 2 was quiet in 6/6.
No parser reset or MISO clamp was used. Raw mode bits independently checked.
Conclusion: reducing FPGA HMISO drive did not suppress the failure.
DD29 regenerates the FPGA signal before driving HDMI through R132 47 ohm.

Original c7531465 bitstream restored; frontend_ready=0xfff; power healthy;
all twelve physical ADC bank-A captures passed on the first attempt.
Kasli output directions/OE remained driven. No clock-chip, MCU, CPLD or flash writes.

The first run failed during JTAG server startup, before FPGA programming,
because the Docker SATA filesystem was full. Its logs are preserved in raw.tar.gz.
The successful second run completed with exit code 0. Old inactive extraction
files were preserved on NVMe with checksum comparison before retrying.

checkpoint-and-bit.tar.gz preserves the routed baseline and DRIVE4 result.
Both retain RTL ID 30096dcc; hashes and port property receipts distinguish them.
Source and protocol: ../miso_drive/. Plots are regenerated from summary.json;
analyze.py validates raw captures and generates summary.json.

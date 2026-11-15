# PM12 MISO output drive experiment

The baseline HMISO pin F24 is LVCMOS33, bank 14, DRIVE 12, SLEW SLOW.
The minimum supported LVCMOS33 drive in this HR bank is 4 mA
([AMD UG471, Table 1-8](https://docs.amd.com/api/khub/documents/IbGcnPFe6eF19RHma_Y~IA/content)).
This is output drive strength, not a constant-current limiter; logic voltage remains 3.3 V.

`query.tcl` inspects the routed baseline. `build.tcl` changes only HMISO DRIVE
to 4 in the existing routed diagnostic checkpoint; no logic synthesis or rerouting.
Both variants intentionally retain RTL ID 30096dcc. Identify them by bitstream SHA-256
and the port-property receipt, not RTL ID alone.

Important schematic qualification: FIT_PM12v1.1 sheet 4 routes FPGA HMISO through
DD29 SN74LVC1G17DBV (3.3 V), then R132 47 ohm, to HDMI PM_SPI_MISO.
The FPGA drive change therefore affects the input of DD29; DD29 still drives the cable.
A successful change would not by itself identify the electrical coupling mechanism.

`test_drive.py` acquires PM12, Kasli and programmer leases, verifies MCU serial/DNA,
then compares normal SPI in a 12 -> 4 -> 12 mA sequence with direct SYS reset captures.
Parser reset and MISO clamp remain disabled. It checks SPI reply words as well as resets,
keeps Kasli outputs driven, and restores original c7531465 followed by power/ADC checks.
A quiet 4 mA result is only informative if 12 mA positive controls reproduce the reset.

Run on Optiplex only, using the Kasli bringup Python environment:

```sh
/home/codex-hil/kasli-diot-bringup/.venv/bin/python \
  diagnostics/pm12/system/miso_drive/test_drive.py \
  --work /srv/codex-hil-nvme/pm12-miso-drive-20261115 \
  --output-name hardware02
```

Heavy checkpoint/bitstream work belongs on Dell using its build slots.

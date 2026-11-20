# CDCE source and MCU control —20 November2026

Leased UART readback, no PLL profile/reference/EEPROM/reset changes. Twelve R8
snapshots,16:35:46–16:35:52UTC, all20009D28: selected source PRIMARY, PLL lock pin
high. RS before/after agrees PRIMARY/LOCKED. PRIMARY is the external/HDMI input
in the established PM12 mapping. This confirms selected source at those instants,
not external waveform quality, continuous lock, or absence of sub-poll transitions.

The deployed diagnostic firmware programs CDCE62005. Its PLL defaults are FLASH
constants, not copied MCU EEPROM settings. The startup sequence loads10words
at0x2916; R5=40040F35 selects AUX. The PLL status ISR conditionally writes
R5=40040FF5 and sets a GPIO, enabling automatic PRI→SEC→AUX selection without
changing output dividers. Timer power-state logic can call defaults reload.
Thus it is not a set-once-and-forget configuration, and logging reference/lock
transitions is relevant. No claim that this mechanism caused the current fault.

The legacy PC command loads a DIFFERENT9word table at0x293e. Do not use PC as a
read-only status command or benign reset; old experiments demonstrated unwanted
clock/transport changes. @PLL selects/reads R8 only, not a dump of R0..R7. RS
LOCKED or a stable R8 series does not establish the intended divider/filter profile.
A next investigation should read R0..R7 via a reviewed non-profile-writing path
and compare with firmware words, while recording source/lock/reset events.

References: firmware paths/hashes in firmware-profile.json;
FIT_PM_FW_uPC/docs/eeprom_map.md and recovered_exact/src/pll_status_interrupt.c;
TI CDCE62005 datasheet register5/source selection and register8 status:
https://www.ti.com/lit/ds/symlink/cdce62005.pdf

Raw data remain staged for operator-labelled board2, FPGA DNA still unbound in
this receipt. Copied EEPROM serial1803 is not used as a unique board identifier.
No board-DNA enrollment or FPGA/IPbus qualification was performed here.

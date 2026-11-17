# USB route guard before requested channel3 measurements

Owner requested continuing after channel4. Native ff2f746c/MCU1803/power guards passed.
Active/inhibited probes on physical3 show negligible response; no full ADC/integrator3 scan ran.
A subsequent control probe on physical4 responds -1776.83/-1761.33code/V;
physical3 response -1.15/-0.39code/V. DAC0/1 still reach ADC4 at this observation.
This is a wiring-route diagnostic, not an ADC3 hardware failure or qualification.

All prior selected measurement results remain unchanged. Native captures, executed
sources and cleanup records are retained. External DAC01=1/1V,23=1.024/2.048V;
route probes restored their original inhibited bypass/monitor state, TCA0.
No FPGA/MCU/CPLD/clock/Kasli direction changes or SMU access. Leases released.
Both USB must be moved to3: DAC01→J8,23→J6, before the next full scan.
The104-page measurement report remains current; these route checks add no qualified ADC3 coverage.

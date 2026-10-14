#ifndef PM_HW_DIAG_H
#define PM_HW_DIAG_H
#include <stdint.h>
enum pm_diag_result { PM_DIAG_OK, PM_DIAG_POWER, PM_DIAG_BUSY, PM_DIAG_TIMEOUT, PM_DIAG_ARGUMENT };
uint8_t pm_diag_temp(uint8_t reg,uint16_t *value);
uint8_t pm_diag_tdc(uint8_t chip,uint8_t reg,uint16_t *value);
uint8_t pm_diag_pll(uint32_t *value);
#ifdef __AVR__
#include <avr/io.h>
static inline uint8_t pm_read8(uint16_t a) { return *(volatile uint8_t *)a; }
static inline void pm_write8(uint16_t a,uint8_t v) { *(volatile uint8_t *)a=v; }
static inline uint8_t pm_irq_enter(void) { uint8_t s=SREG;asm volatile("cli" ::: "memory");return s; }
static inline void pm_irq_leave(uint8_t s) { asm volatile("" ::: "memory");SREG=s; }
#else
uint8_t pm_read8(uint16_t a);
void pm_write8(uint16_t a,uint8_t v);
uint8_t pm_irq_enter(void);
void pm_irq_leave(uint8_t s);
#endif
#endif

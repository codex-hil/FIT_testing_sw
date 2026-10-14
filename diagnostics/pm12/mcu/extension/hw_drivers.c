/* Read-only device operations, main-loop only. No reset, DAC, power, EEPROM,
 * flash or I2C writes. IRQ masking serializes against the recovered PLL ISR;
 * each transaction is finite, with at most 128 SPI polls per byte. Hardware
 * interrupt latency and electrical ownership still need validation. */
#include "hw_diag.h"
#define A 0x600u
#define B 0x620u
#define C 0x640u
#define E 0x680u
#define F 0x6a0u
#define PM_SPIC 0x8c0u
#define DIR 0u
#define DIRSET 1u
#define DIRCLR 2u
#define OUT 4u
#define SET 5u
#define CLR 6u
#define IN 8u
static uint8_t powered(void) { return (pm_read8(E+OUT)&4) && (pm_read8(E+IN)&10)==10; }
static void restore_bits(uint16_t port,uint8_t mask,uint8_t out)
{ pm_write8(port+CLR,mask & (uint8_t)~out);pm_write8(port+SET,mask & out); }
static uint8_t temp_byte(uint8_t tx)
{
 uint8_t rx=0;
 for(uint8_t n=0;n<8;++n) {
  pm_write8(A+CLR,2);pm_write8(A+((tx&128)?SET:CLR),8);
  pm_write8(A+SET,2);rx=(uint8_t)((rx<<1)|((pm_read8(A+IN)>>2)&1));tx<<=1;
 }
 return rx;
}
uint8_t pm_diag_temp(uint8_t reg,uint16_t *value)
{
 if(reg>3)return PM_DIAG_ARGUMENT;
 uint8_t irq=pm_irq_enter(),result=PM_DIAG_OK;
 uint8_t old=pm_read8(A+OUT);
 if(!powered())result=PM_DIAG_POWER;
 else if((pm_read8(A+DIR)&0x1a)!=0x1a || !(old&16))result=PM_DIAG_BUSY;
 else {
  pm_write8(A+CLR,16);(void)temp_byte((uint8_t)(0x40|(reg<<3)));
  uint16_t v=temp_byte(0);if(reg==2)v=(uint16_t)((v<<8)|temp_byte(0));
  pm_write8(A+SET,16);restore_bits(A,0x1a,old);*value=v;
 }
 pm_irq_leave(irq);return result;
}
static void clock_tdc(void) { pm_write8(B+SET,1);pm_write8(B+CLR,1); }
static void send_tdc_bit(uint8_t bit) { pm_write8(B+(bit?SET:CLR),2);clock_tdc(); }
uint8_t pm_diag_tdc(uint8_t chip,uint8_t reg,uint16_t *value)
{
 if(chip>2)return PM_DIAG_ARGUMENT;
 uint8_t irq=pm_irq_enter(),result=PM_DIAG_OK;
 uint8_t old=pm_read8(B+OUT),dir=pm_read8(B+DIR),select=(uint8_t)(4u<<chip);
 if(!powered() || !(old&32) || !(pm_read8(B+IN)&64))result=PM_DIAG_POWER;
 else if((old&0x1c)!=0x1c || (dir&0x1f)!=0x1f)result=PM_DIAG_BUSY;
 else {
  pm_write8(B+CLR,select);send_tdc_bit(1);send_tdc_bit(0);
  for(uint8_t n=0;n<8;++n){send_tdc_bit(reg&128);reg<<=1;}
  pm_write8(B+DIRCLR,2);clock_tdc();uint16_t v=0;
  for(uint8_t n=0;n<16;++n){pm_write8(B+SET,1);v=(uint16_t)((v<<1)|((pm_read8(B+IN)>>1)&1));pm_write8(B+CLR,1);}
  pm_write8(B+SET,select);pm_write8(B+DIRSET,2);clock_tdc();clock_tdc();
  restore_bits(B,0x1f,old);*value=v;
 }
 pm_irq_leave(irq);return result;
}
static uint8_t spi_byte(uint8_t tx,uint8_t *rx)
{
 pm_write8(PM_SPIC+3,tx);
 for(uint8_t n=0;n<128;++n)if(pm_read8(PM_SPIC+2)&128){*rx=pm_read8(PM_SPIC+3);return PM_DIAG_OK;}
 return PM_DIAG_TIMEOUT;
}
uint8_t pm_diag_pll(uint32_t *value)
{
 uint8_t irq=pm_irq_enter(),result=PM_DIAG_OK,old=pm_read8(PM_SPIC),out=pm_read8(F+OUT),rx=0;
 if(!powered())result=PM_DIAG_POWER;
 else if(!(out&16) || (pm_read8(C+OUT)&7)!=7 || !(old&0x40))result=PM_DIAG_BUSY;
 else {
  /* Same 0x8e readback request as recovered FUN_code_001267. No PLL profile writes. */
  pm_write8(PM_SPIC,0xf1);pm_write8(F+CLR,16);
  for(uint8_t n=0;n<4 && result==PM_DIAG_OK;++n)result=spi_byte(n?0:0x8e,&rx);
  pm_write8(F+SET,16);
  uint32_t v=0;
  if(result==PM_DIAG_OK){pm_write8(F+CLR,16);for(uint8_t n=0;n<4 && result==PM_DIAG_OK;++n){result=spi_byte(0,&rx);v|=(uint32_t)rx<<(n*8);}}
  pm_write8(F+SET,16);pm_write8(PM_SPIC,old);
  if(result==PM_DIAG_OK)*value=v;
 }
 pm_irq_leave(irq);return result;
}

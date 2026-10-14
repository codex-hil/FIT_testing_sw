#include "extension.h"
#include "hw_diag.h"
static const PM_FLASH char earg[]="ERR ARGUMENTS\r\n";
static const PM_FLASH char off[]="ERR POWER\r\n",busy[]="ERR BUSY\r\n",timeout[]="ERR TIMEOUT\r\n";
static void hex(uint32_t v,uint8_t digits) { while(digits){uint8_t n=(v>>(--digits*4))&15;pm_console_putc(n<10?'0'+n:'A'+n-10);} }
static void line(void){pm_console_putc('\r');pm_console_putc('\n');}
static uint8_t result(uint8_t s){if(s==PM_DIAG_OK)return 1;pm_console_write(s==PM_DIAG_POWER?off:s==PM_DIAG_BUSY?busy:s==PM_DIAG_TIMEOUT?timeout:earg);return 0;}
void pm_command_hw(const char *args)
{
 if(*args){pm_console_write(earg);return;}
 uint8_t saved=pm_irq_enter();uint8_t ports[6],state[12];
 for(uint8_t n=0;n<6;++n)ports[n]=pm_read8(0x608u+n*32u);
 for(uint8_t n=0;n<12;++n)state[n]=pm_read8(0x2157u+n);
 pm_irq_leave(saved);
 static const PM_FLASH char banner[]="HW V2 PORTS A..F=";pm_console_write(banner);
 for(uint8_t n=0;n<6;++n)hex(ports[n],2);
 static const PM_FLASH char label[]=" STATE 2157..2162=";pm_console_write(label);
 for(uint8_t n=0;n<12;++n)hex(state[n],2);
 line();
}
void pm_command_temp(const char *args)
{
 if(*args){pm_console_write(earg);return;}
 static const PM_FLASH char label[]="ADT7311 REG=";
 for(uint8_t reg=0;reg<4;++reg){uint16_t v=0;if(!result(pm_diag_temp(reg,&v)))return;pm_console_write(label);hex(reg,2);pm_console_putc(' ');hex(v,reg==2?4:2);line();}
}
void pm_command_tdc(const char *args)
{
 /* Chip decimal 0..2, followed by exactly two uppercase hex address digits. */
 if(args[0]<'0'||args[0]>'2'||args[1]!=' '||!args[2]||!args[3]||args[4]){pm_console_write(earg);return;}
 uint8_t address=0;
 for(uint8_t n=2;n<4;++n){uint8_t c=args[n],v;if(c>='0'&&c<='9')v=c-'0';else if(c>='A'&&c<='F')v=c-'A'+10;else{pm_console_write(earg);return;}address=(address<<4)|v;}
 uint16_t v=0;if(!result(pm_diag_tdc(args[0]-'0',address,&v)))return;
 static const PM_FLASH char label[]="THS788 ";pm_console_write(label);pm_console_putc(args[0]);pm_console_putc(' ');hex(address,2);pm_console_putc(' ');hex(v,4);line();
}
void pm_command_pll(const char *args)
{
 if(*args){pm_console_write(earg);return;}uint32_t v=0;if(!result(pm_diag_pll(&v)))return;
 static const PM_FLASH char label[]="CDCE62005 ";pm_console_write(label);hex(v,8);line();
}

void pm_command_pgtime(const char *args)
{
 if(*args){pm_console_write(earg);return;}
 uint8_t irq=pm_irq_enter();
 uint8_t state=pm_read8(0x0a2a),overflow=pm_read8(0x0a2b);
 uint16_t ticks=pm_read8(0x0a28);ticks|=(uint16_t)pm_read8(0x0a29)<<8;
 if(state==1){ticks=pm_read8(0x0a20);ticks|=(uint16_t)pm_read8(0x0a21)<<8;}
 pm_irq_leave(irq);
 static const PM_FLASH char label[]="PGTIME STATE=";pm_console_write(label);hex(state,2);
 static const PM_FLASH char t[]=" TICKS=";pm_console_write(t);hex(ticks,4);
 static const PM_FLASH char o[]=" OVF=";pm_console_write(o);hex(overflow,2);
 static const PM_FLASH char u[]=" US_NOMINAL=";pm_console_write(u);hex((uint32_t)ticks*32u,8);line();
}

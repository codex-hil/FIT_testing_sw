#!/usr/bin/env python3
"""Recheck one repaired CFD monitor; inhibit every shared mux, preserve analog controls."""
import argparse,contextlib,datetime,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(P/'acceptance'),str(P/'cfd_simulator'),str(P/'ipbus_adc'),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware','/home/codex-hil/lab-instruments']
from lease import acquire
from station import console
from console import ConsoleI2C,Registers
from mcp23017 import afe_route,MCP23017Monitor,report_voltage
from channel_settings import connected_channels,require_serial_reply,snapshot_sources
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
from client import Client
from campaign_monitor_adapter import voltage_checks
from labinstruments.transport import Transport
from labinstruments.drivers import Driver
from smu_voltage import parse_voltage

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--connected',nargs=4,type=int,required=True);p.add_argument('--channel',type=int,required=True);p.add_argument('--host',default='192.168.2.19');p.add_argument('--repair-note',required=True);a=p.parse_args()
 channels,_=connected_channels(a.connected,[a.channel]);a.out.mkdir(parents=True,exist_ok=False)
 r=dict(pass_=False,physical_channel=a.channel,connected_channels=channels,repair_note=a.repair_note,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),commands=[],readings=[],gpio_before={},gpio_after={})
 r['executed_sources']=snapshot_sources(a.out,['__main__','lease','station','console','mcp23017','channel_settings','pm12_power','pm12_console_regression','client','campaign_monitor_adapter','smu_voltage','labinstruments.transport','labinstruments.drivers'])
 def save():(a.out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
 try:
  with contextlib.ExitStack()as st:
   for n in sorted(['atmel-ice-J41800043065','pm12-210249A73E43','kasli-diot-00001','b2910bl-MY63320299']):st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock')))
   io=st.enter_context(Transport(dict(kind='tcp',host=a.host,port=5025,timeout=8,delay=.01)));meter=Driver(io,'b2910bl','MY63320299');r['instrument']=meter.identify();meter.off()
   u=st.enter_context(console(dict(uart='/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0')));r['pgood']=wait_power_good(u,capture);r['mcu']=capture(u,'RS');require_serial_reply(r['mcu']['reply'],'1803');bus=ConsoleI2C(u,capture);c=Client();st.callback(c.close);
   try:
    r['fpga']=c.read(0,3);assert r['fpga'][:2]==[0x504d1202,0x10002]
   except TimeoutError:r['fpga_unavailable']='IPbus timeout; MCU-only monitor measurement, no FPGA programming'
   def q(command):
    value=io.query(command);r['commands'].append(dict(query=command,reply=value));return value
   def w(command):io.write(command);r['commands'].append(dict(write=command))
   def off_all(key):
    for ch in channels:
     with bus.routed(*afe_route(ch)):
      regs=Registers(bus);before={str(k):regs.read(k)for k in [0,1,0x14,0x15]};MCP23017Monitor(regs).initialize_monitor().off();assert regs.read(0x12)&8
      r[key][str(ch)]=before if key=='gpio_before'else{str(k):regs.read(k)for k in [0,1,0x14,0x15]}
   try:
    for addr in [0x70,0x71]:bus.mux(addr,0)
    off_all('gpio_before');w('ABOR');w('OUTP:ON:AUTO OFF')
    for _ in range(10):
     if int(q('SYST:ERR?').split(',')[0])==0:break
    for command in ['SOUR:FUNC:MODE CURR','SOUR:CURR:MODE FIX','SOUR:CURR 0','SOUR:CURR:RANG 1e-6','SENS:VOLT:PROT 6','SENS:REM OFF','SENS:FUNC "VOLT"','SENS:VOLT:RANG:AUTO OFF','SENS:VOLT:RANG 20','SENS:VOLT:NPLC 1','TRIG:ACQ:SOUR AINT','TRIG:ACQ:COUN 1','FORM:ELEM:SENS VOLT,TIME,STAT']:
     w(command);assert int(q('SYST:ERR?').split(',')[0])==0
    r['settings']={k:q(k)for k in ['OUTP?','SOUR:FUNC:MODE?','SOUR:CURR?','SENS:REM?']};assert r['settings']['OUTP?']=='0' and r['settings']['SOUR:FUNC:MODE?']=='CURR' and float(r['settings']['SOUR:CURR?'])==0 and r['settings']['SENS:REM?']=='0'
    w('OUTP ON');assert q('OUTP?')=='1'
    with bus.routed(*afe_route(a.channel)):
     regs=Registers(bus);mux=MCP23017Monitor(regs).initialize_monitor()
     try:
      for selection in list(range(8))+[7]:
       require_power_good(u,capture);mux.select(selection);time.sleep(.2);pins=regs.read(0x12);assert pins&15==[0,4,2,6,1,5,3,7][selection]
       values=[parse_voltage(q('READ?'))for _ in range(5)];raw=sum(v[0]for v in values)/len(values);row=dict(mux_channel=selection,gpioa=pins,samples=[dict(volts=v,time=t,status=s)for v,t,s in values],converted=report_voltage(selection,raw));r['readings'].append(row);save();print(selection,row['converted'],flush=True)
     finally:mux.off()
    r['checks']=voltage_checks([x['converted']['volts']for x in r['readings'][:8]]);r['pgood_after']=require_power_good(u,capture);r['pass_']=all(r['checks'])
   finally:
    meter.off();off_all('gpio_after')
    for addr in [0x70,0x71]:bus.mux(addr,0)
    r['final_tca']={str(k):bus.mux(k)for k in [0x70,0x71]};r['final_smu']={k:q(k)for k in ['OUTP?','OUTP:OFF:MODE?','OUTP:ON:AUTO?','SOUR:FUNC:MODE?','SOUR:CURR?','SENS:REM?','SYST:ERR?']};r['i2c']=bus.records
    for ch in channels:
     before,after=r['gpio_before'][str(ch)],r['gpio_after'][str(ch)];assert before['0']&0xf0==after['0']&0xf0 and before['20']&0xf0==after['20']&0xf0 and before['1']==after['1']and before['21']==after['21']and after['20']&8
    assert set(r['final_tca'].values())=={0}and r['final_smu']['OUTP?']=='0'and r['final_smu']['OUTP:OFF:MODE?']=='HIZ'and float(r['final_smu']['SOUR:CURR?'])==0
 except BaseException as error:r['error']=repr(error);r['pass_']=False;raise
 finally:r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
 if not r['pass_']:raise SystemExit('Monitor functional checks failed; retain raw result')
 print('REPAIRED_MONITOR_PASS',flush=True)
if __name__=='__main__':main()

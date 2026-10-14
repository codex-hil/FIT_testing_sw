#!/usr/bin/env python3
"""Read PM12 diagnostic extensions. Does not program, reset or toggle power.
Requires an explicitly identified PM12 UART; take the PM12 board lease.
"""
import argparse,fcntl,json,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--port',required=True);p.add_argument('--baud',type=int,default=115200);p.add_argument('--rtscts',action='store_true');p.add_argument('--out',type=Path,required=True);args=p.parse_args()
 import serial
 with open('/home/codex-hil/.cache/pm12-210249A73E43.lock','a+') as lease:
  fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
  # Construct closed to suppress pyserial's default DTR assertion on open.
  uart=serial.Serial(port=None,baudrate=args.baud,timeout=.05,write_timeout=1,rtscts=args.rtscts)
  uart.dtr=False;uart.rts=False;uart.port=args.port;uart.open()
  records=[]
  try:
   uart.reset_input_buffer()
   for command,lines in [('PING',1),('HW',1),('TEMP',4),('TDC 0 83',1),('TDC 1 83',1),('TDC 2 83',1),('PLL',1),('HW',1)]:
    request=('@'+command+'\r').encode();uart.write(request)
    end=time.monotonic()+2;data=bytearray()
    while time.monotonic()<end and data.count(b'\n')<lines:
     chunk=uart.read(128);data.extend(chunk)
     if b'ERR ' in data and b'\n' in data:break
     if len(data)>1024:raise RuntimeError('Unbounded reply')
    reply=data.decode('ascii',errors='replace');records.append({'command':command,'reply':reply,'timestamp':time.time()})
    if command=='PING' and reply!='PONG\r\n':raise RuntimeError('PM12 diagnostic firmware not identified')
    if data.count(b'\n')<lines or b'ERR ' in data:raise RuntimeError('Command failed: '+command+' '+reply)
   print(json.dumps(records,indent=2))
  finally:
   uart.close();args.out.write_text(json.dumps({'port':args.port,'baud':args.baud,'rtscts':args.rtscts,'records':records,'hardware_test':'read-only UART command capture; raw device IDs require interpretation'},indent=2)+'\n')
if __name__=='__main__':main()

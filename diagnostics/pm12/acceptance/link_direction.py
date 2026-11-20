#!/usr/bin/env python3
"""Read-only PM RX/TX isolation using USER1 and Kasli bridge counters.

No resets, programming, output-direction changes or retried PM requests.
Frame counters include background Ethernet traffic; quiet controls are retained.
"""
import argparse,contextlib,json,subprocess,time,datetime,uuid,shutil
from pathlib import Path
import board_session as b
from boundary import physical_identity
from station import load_dependencies,jtag_command

def decode(raw):
 v=int(raw.strip(),16)
 if v&0xffffffff!=0x504d5a04 or (v>>208)&0xffffffff!=0x504d4442:raise ValueError('Unsupported JTAG network report')
 flags=(v>>240)&0xffffffff
 names=['link','cap_lock','net_lock','got_ip','net_reset','gt_pll_lock','tx_ready','rx_ready','tx_mmcm_lock','rx_mmcm_lock','phy_request','startup']
 d={'flags':{name:bool(flags&(1<<i)) for i,name in enumerate(names)},'sys_tick':(v>>32)&0xffffffff}
 for name,bit,width in [('rx_frames',272,32),('tx_frames',304,32),('rx_bytes',336,32),('tx_bytes',368,32),('rx_error_cycles',400,16),('ipbus_strobe_cycles',432,32),('net_tick',464,32)]:d[name]=(v>>bit)&((1<<width)-1)
 return d

def deltas(before,after):
 return {k:(after[k]-before[k])&((1<<(16 if k=='rx_error_cycles' else 32))-1) for k in before if k!='flags'}

def run(cfg,root,requests=20):
 if not 1<=requests<=100:raise ValueError('Requests1..100')
 out=Path(root)/b.uid(cfg)/'setup'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-rx-tx-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
 b.write(out/'station.json',cfg);shutil.copy2(Path(__file__),out/'executed-link-direction.py')
 r={'board_uid':b.uid(cfg),'status':'ERROR','started_utc':b.now(),'requests':[],'stages':{},'scope':'Read-only JTAG/bridge frame counts and single-shot IPbus reads, no host retransmission. Quiet controls expose background traffic; no packet capture privileges.'}
 def save():b.write(out/'result.json',r)
 script='source '+str(b.PM/'adc/tools/common.tcl')+'\npm12_open\nscan_ir_hw_jtag 102 -tdi 3fffffffffffffffffffffffc2\n'
 script+='''foreach label {q0 q1 q2 q3} {
 for {set sample 0} {$sample<3} {incr sample} {
  set report [scan_dr_hw_jtag 524 -tdi 0]
  set f [open [file join $::env(PM12_PAYLOAD) "$label-$sample.txt"] w]
  puts $f $report
  close $f
  after 25
 }
 set f [open [file join $::env(PM12_PAYLOAD) "$label.ready"] w]; puts $f ready; close $f
 if {$label ne "q3"} {
  set deadline [expr {[clock milliseconds]+90000}]
  while {![file exists [file join $::env(PM12_PAYLOAD) "$label.done"]]} {
   if {[clock milliseconds]>$deadline} {error "Host stage timeout"}
   after 20
  }
 }
}
pm12_close
exit
'''
 (out/'observe.tcl').write_text(script)
 load_dependencies(cfg);from client import Client
 with b.locks(cfg):
  try:
   r['physical_identity']=physical_identity(cfg,out/'physical-identity');save()
   local=dict(cfg,jtag_workspace=str(out/'jtag-work'))
   with jtag_command(local,out) as prefix:
    with (out/'jtag.log').open('w') as log:
     proc=subprocess.Popen(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(out/'observe.tcl'),'-tclargs',cfg['jtag_cable'],cfg.get('hw_server','localhost:3121'),str(out),'0'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
     pm=Client();kasli=Client(cfg.get('kasli_ip','192.168.2.241'))
     def stage(label):
      end=time.monotonic()+100
      while not (out/(label+'.ready')).exists():
       if proc.poll() is not None or time.monotonic()>end:raise RuntimeError('JTAG observer ended before '+label)
       time.sleep(.03)
      samples=[decode((out/(label+f'-{i}.txt')).read_text()) for i in range(3)]
      z=kasli.read(0x120//4,8);assert z[0]==1 and z[1]==1 and z[6:]==[4096,0x42524731],z
      r['stages'][label]={'utc':b.now(),'pm_samples':samples,'pm':samples[-1],'kasli':dict(zip(['enabled','lan_link','to_lan','to_pm','drop_to_lan','drop_to_pm','depth','abi'],z)),'pm_phy_status':kasli.read(0x104//4)[0]};save()
     def done(label):(out/(label+'.done')).write_text('done\n')
     try:
      assert kasli.read(0,2)==[0x52504831,0x10002]
      stage('q0');time.sleep(2);done('q0');stage('q1')
      for i in range(requests):
       start=time.monotonic();row={'index':i,'utc':b.now()}
       try:
        v=pm.transact(0,0,count=1);row['reply']=v;row['ok']=v==[0x504d1202]
       except Exception as error:row['ok']=False;row['error']=repr(error)
       row['elapsed_s']=time.monotonic()-start;r['requests'].append(row);save();time.sleep(.1)
      time.sleep(1);done('q1');stage('q2');time.sleep(2);done('q2');stage('q3');proc.wait(timeout=30);assert proc.returncode==0
      for label,left,right in [('quiet_before','q0','q1'),('traffic','q1','q2'),('quiet_after','q2','q3')]:
       x=r['stages'][left];y=r['stages'][right];r[label]={'pm':deltas(x['pm'],y['pm']),'kasli':{k:(y['kasli'][k]-x['kasli'][k])&0xffffffff for k in ['to_pm','to_lan','drop_to_lan','drop_to_pm']}}
      r['host_sent']=requests;r['host_good_replies']=sum(x['ok'] for x in r['requests']);r['kasli_read_timeout_events']=kasli.read_retry_events;r['pm_host_retransmissions']=pm.read_retry_events;r['status']='OBSERVED'
     finally:
      pm.close();kasli.close()
      if proc.poll() is None:proc.terminate();proc.wait(timeout=15)
  except BaseException as error:r['error']=repr(error)
  finally:r['finished_utc']=b.now();save();b.write(out/'files.sha256.json',b.files(out))
 print(json.dumps({'path':str(out),'status':r['status'],'sent':r.get('host_sent'),'good':r.get('host_good_replies'),'traffic':r.get('traffic'),'quiet_before':r.get('quiet_before'),'quiet_after':r.get('quiet_after'),'error':r.get('error')},indent=2));return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--station',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--requests',type=int,default=20);a=p.parse_args();raise SystemExit(0 if run(b.read(a.station),a.root,a.requests)['status']=='OBSERVED' else 1)

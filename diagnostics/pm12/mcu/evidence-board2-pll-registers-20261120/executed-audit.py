import sys,json,hashlib,contextlib,datetime,subprocess,re,time
from pathlib import Path
P=Path(__file__).parent;O=P/'hardware';O.mkdir(exist_ok=False)
A=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance');sys.path[:0]=[str(A),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from lease import acquire
from station import console
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
cfg=json.loads((A/'profiles/optiplex-session.example.json').read_text());base=['avrdude','-c','atmelice_pdi','-p','x128a3u','-P','usb:J41800043065','-B','10','-u'];mem=['flash','boot','eeprom','fuse0','fuse1','fuse2','fuse4','fuse5','lock','usersig','prodsig','signature'];r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operator_label':'board2','board_uid':None,'status':'ERROR','scope':'Temporary application-only extension for R0..R8 read; original application restored. No PLL profile/EEPROM, MCU EEPROM/fuse/boot or FPGA writes.'};attempted=False
candidate=(P/'source/development/build/development.bin').read_bytes();original=Path('/home/codex-hil/FIT_PM_FW_uPC/development/build/development.bin').read_bytes();assert hashlib.sha256(original).hexdigest()=='f49643c80c6189afebdaa3f7301f4ecebacb55645e60456f66831106d38b9464'
def save():(O/'result.json').write_text(json.dumps(r,indent=2)+'\n')
def run(cmd,name,timeout=240):
 with (O/name).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
def reads(dest):return sum((['-U',m+':r:'+str(dest/(m+'.bin'))+':r'] for m in mem),[])
def check(dest,app):
 raw=(dest/'flash.bin').read_bytes().ljust(0x22000,b'\xff');assert raw[:0x20000]==app
 equal={m:(dest/(m+'.bin')).read_bytes()==(O/'backup'/(m+'.bin')).read_bytes() for m in mem[1:]};assert all(equal.values()),equal;return equal
with contextlib.ExitStack() as st:
 for n in sorted(['pm12-210249A73E43','atmel-ice-J41800043065','kasli-diot-00001']):st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock')))
 try:
  with console(cfg) as u:
   r['pgood_before']=wait_power_good(u,capture);r['rs_before']=capture(u,'RS');r['pll_before']=capture(u,'@PLL');save();assert 'FPGA not ready' in r['rs_before']['reply'],'FPGA may be live; do not reset MCU without coordinated SRAM restore'
  backup=O/'backup';backup.mkdir();run(base+['-n']+reads(backup),'backup.log');old=(backup/'flash.bin').read_bytes().ljust(0x22000,b'\xff');assert old[:0x20000]==original[:0x20000],'Unexpected resident MCU application';assert hashlib.sha256((backup/'prodsig.bin').read_bytes()).hexdigest()=='f1b955294628e001d491e6117e1ae48886342fed01f4536b8dd731f2b083c11c','Wrong MCU'
  (O/'original-application.bin').write_bytes(old[:0x20000]);(O/'audit-application.bin').write_bytes(candidate[:0x20000]);r['backup_sha256']=hashlib.sha256(old).hexdigest();r['temporary_source_sha256']=hashlib.sha256(candidate).hexdigest();save()
  writebase=['avrdude','-C','+'+str(A.parent/'mcu/pdi-application-only.conf'),'-c','atmelice_pdi','-p','pm12_full_app','-P','usb:J41800043065','-B','10','-u']
  dest=O/'candidate-readback';dest.mkdir();attempted=True;run(writebase+['-U','app_full:w:'+str(O/'audit-application.bin')+':r']+reads(dest),'candidate-write.log');r['candidate_unchanged_protected']=check(dest,candidate[:0x20000]);save()
  with console(cfg) as u:
   r['pgood_audit']=wait_power_good(u,capture);r['dumps']=[]
   for index in range(3):
    require_power_good(u,capture);row=capture(u,'@PLL ALL',limit=8);row['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();registers={int(k,16):int(v,16) for k,v in re.findall(r'CDCE62005 REG=([0-9A-F]{2}) ([0-9A-F]{8})',row['reply'])};assert set(registers)==set(range(9)),row;row['registers']={str(k):f'{v:08X}' for k,v in registers.items()};r['dumps'].append(row);save()
   r['lock_samples']=[]
   for index in range(40):
    require_power_good(u,capture);row=capture(u,'@PLL');row['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();r['lock_samples'].append(row);save();time.sleep(.1)
   r['sensor_checks']=[]
   for command in ['RS','@TEMP','@POWER']:
    require_power_good(u,capture);r['sensor_checks'].append(capture(u,command))
   assert 'ADT7311 REG=03 C3' in r['sensor_checks'][1]['reply'];assert 'ERR ' not in r['sensor_checks'][2]['reply'];save()
  r['acquisition']='PASS'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  if attempted:
   dest=O/'restored';dest.mkdir();run(writebase+['-U','app_full:w:'+str(O/'original-application.bin')+':r']+reads(dest),'restore.log');r['restored_protected']=check(dest,old[:0x20000]);r['original_application_restored']='PASS';save()
   with console(cfg) as u:
    r['pgood_restored']=wait_power_good(u,capture);r['post_restore']=[]
    for command in ['RS','@PLL','@TEMP','@POWER']:
     require_power_good(u,capture);r['post_restore'].append(capture(u,command))
   assert 'ADT7311 REG=03 C3' in r['post_restore'][2]['reply'];assert 'ERR ' not in r['post_restore'][3]['reply'];r['post_restore_functional']='PASS'
  r['status']='PASS' if r.get('acquisition')=='PASS' and r.get('original_application_restored')=='PASS' else 'ERROR';r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
print(json.dumps({'path':str(O),'status':r['status'],'dumps':r.get('dumps'),'post_restore':r.get('post_restore')}))

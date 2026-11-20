`timescale 1ns/1ps
module control_tb;
 reg clk=0;
 always #12.5 clk=~clk;
 // Deliberately hold USER1 TCK low throughout all USER2 transactions.
 reg tck=0,reset=0,cap=0,shift=0,sel=0,tdi=0;
 reg tck2=0,reset2=0,cap2=0,update2=0,sel2=0,shift2=0,tdi2=0;
 wire reset_toggle,freeze_request,frozen;
 wire [1567:0] monitor_report;
 link_monitor monitor(.clk(clk),.reset_toggle(reset_toggle),.freeze_request(freeze_request),.pins(168'b0),.frozen(frozen),.report(monitor_report));
`ifdef LEGACY
 jtag_report transport(.tck(tck),.reset(reset),.capture1(cap),.shift1(shift),.sel1(sel),.tdi(tdi2),.update2(update2),.sel2(sel2),.shift2(shift2),.report({192'b0,monitor_report}),.tdo1(),.reset_toggle(reset_toggle),.freeze_request(freeze_request));
`else
 jtag_report transport(.tck(tck),.reset(reset),.capture1(cap),.shift1(shift),.sel1(sel),.tdi(tdi),.tck2(tck2),.reset2(reset2),.capture2(cap2),.update2(update2),.sel2(sel2),.shift2(shift2),.tdi2(tdi2),.report({192'b0,monitor_report}),.tdo1(),.reset_toggle(reset_toggle),.freeze_request(freeze_request));
`endif
 task tick2;
 begin #10;tck2=1;#10;tck2=0;#10;end
 endtask
 task command(input [1:0] value);
 begin
  sel2=1;cap2=1;tick2();cap2=0;
  shift2=1;tdi2=value[0];tick2();tdi2=value[1];tick2();shift2=0;
  update2=1;tick2();update2=0;sel2=0;#500;
 end
 endtask
 integer i,fd;
 reg [31:0] held;
 initial begin
  #1000;
  for(i=0;i<3;i=i+1) begin
   command(1);#1000;
   if(reset_toggle!==1 || freeze_request!==0)$fatal(1,"USER2 run command failed without USER1 clock");
   command(3);
   if(frozen!==1)$fatal(1,"freeze not acknowledged");
   held=monitor_report[63:32];#1000;
   if(monitor_report[63:32]!==held)$fatal(1,"frozen counter changed");
   command(1);#1000;
   if(frozen!==0 || monitor_report[63:32]<=held)$fatal(1,"resume failed");
   command(0);
   if(reset_toggle!==0 || freeze_request!==0)$fatal(1,"reset command failed");
  end
  // Closing the TAP must not recommit a stale USER2 word.
  command(3);reset2=1;update2=1;sel2=1;tick2();reset2=0;tick2();update2=0;sel2=0;
  if(freeze_request!==1 || reset_toggle!==1)$fatal(1,"stale reset commit");
  fd=$fopen("control-tb-pass.txt","w");$fdisplay(fd,"CONTROL_TB_PASS");$fclose(fd);
  $display("CONTROL_TB_PASS");$finish;
 end
endmodule

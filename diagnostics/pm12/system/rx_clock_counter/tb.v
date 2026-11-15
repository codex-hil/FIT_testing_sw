`timescale 1ns/1ps
module tb;
 reg refclk=0,mclk=0,gtref=0,sysclk=0;reg men=1;
 always #5 refclk=~refclk;
 always #7.5 if(men)mclk=~mclk;else mclk=0;
 always #3 gtref=~gtref;
 always #7.5 sysclk=~sysclk;
 reg arm=0,sysreset=0,rxdone=1;reg[12:0]idx=0;reg[3:0]csr=0;wire[31:0]cd,data;
 rx_clock_counter #(.WINDOW(96),.DEPTH(16),.TIMEOUT(4000)) dut(refclk,mclk,gtref,sysclk,arm,1'b1,1'b1,sysreset,1'b1,rxdone,1'b1,idx,csr,cd,data);
 task start;begin arm=~arm;wait(dut.active);repeat(20)@(posedge refclk);end endtask
 task getword(input integer address,output reg[31:0]v);begin idx=address;repeat(3)@(posedge sysclk);#1;v=data;end endtask
 reg[31:0]w0,w1,w2,w3;integer i,physical,found,lastid;reg[31:0]saved;
 task normal_check;begin
 wait(dut.frozen);repeat(5)@(posedge sysclk);csr=2;#1;if(cd!==16)$fatal(1,"saturated count");csr=3;#1;if(cd!==dut.wp)$fatal(1,"oldest pointer");lastid=-1;
 for(i=0;i<16;i=i+1)begin
  physical=(dut.wp+i)%16;getword(physical*4,w0);getword(physical*4+1,w1);getword(physical*4+2,w2);getword(physical*4+3,w3);
  if(i&&w3[15:0]!==lastid+1)$fatal(1,"ring order");lastid=w3[15:0];
  if(!w2[23])begin
   if(w1[15:0]<63||w1[15:0]>65||w1[31:16]<159||w1[31:16]>161||w2[15:0]<63||w2[15:0]>65)$fatal(1,"normal ratios");
   if(w3[31:16]!=96)$fatal(1,"full window length");
  end
 end
 if(dut.triggered)$fatal(1,"unexpected trigger");
 end endtask
 initial begin
 repeat(30)@(posedge refclk);start();normal_check();
 start();wait(dut.window_id==20);men=0;#300;men=1;repeat(400)@(posedge refclk);rxdone=0;repeat(20)@(posedge refclk);rxdone=1;#3;sysreset=1;#22;sysreset=0;wait(dut.frozen);repeat(5)@(posedge sysclk);
 if(!dut.triggered||!dut.invalid_ref||dut.min_m>=60)$fatal(1,"missing trigger/gap/reference qualification");
 found=0;for(i=0;i<16;i=i+1)begin physical=(dut.wp+i)%16;getword(physical*4+1,w1);getword(physical*4+2,w2);if(!w2[23]&&w1[15:0]<60)found=1;end
 if(!found)$fatal(1,"gap not retained in ring");
 getword(((dut.wp+15)%16)*4,w0);saved=w0;#1000;getword(((dut.wp+15)%16)*4,w0);if(w0!==saved)$fatal(1,"frozen RAM changed");
 #1000000;start();normal_check();
 $display("PASS clock ratios, ring wrap/readout, dropped MCLK edges, async SYS reset freeze, invalid RX flag, frozen retention, rearm and source-counter wrap");$finish;
 end
 initial begin #2000000;$fatal(1,"timeout");end
endmodule

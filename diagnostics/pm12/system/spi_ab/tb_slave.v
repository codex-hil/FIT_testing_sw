`timescale 1ns/1ps
module tb;
 reg clk=0,sel=0,mosi=0,locked=1;reg[1:0]mode=0;
 wire miso;wire[15:0]scratch,writes,shift;wire[5:0]state;wire[7:0]addr;reg[15:0]rx;integer max_count;
 ab_slave dut(clk,sel,mosi,locked,mode,miso,scratch,writes,state,addr,shift);
 task frame(input[7:0]address);integer i;reg[31:0]packet;begin
 packet=32'h80000000|({24'd0,address}<<22);rx=0;max_count=0;sel=0;#3;sel=1;
 for(i=31;i>=0;i=i-1)begin mosi=packet[i];#3;clk=1;#3;if(i<16)rx={rx[14:0],miso};clk=0;#3;
 if(state[4:0]>max_count)max_count=state[4:0];if(mode[0]&&state!==0)$fatal(1,"parser not held");end
 sel=0;#3;end endtask
 initial begin
 #2;frame(0);if(rx!==16'h4844||max_count!=31)$fatal;
 mode=2;frame(1);if(rx!==0||max_count!=31||shift!==16'h4d49)$fatal(1,"clamp-only must leave parser active");
 mode=3;frame(0);if(rx!==0||max_count!=0||shift!==16'h4d49)$fatal(1,"held must retain parser data");
 mode=2;frame(0);if(rx!==0||max_count!=31||shift!==16'h4844)$fatal;
 mode=0;frame(1);if(rx!==16'h4d49)$fatal;
 $display("PASS normal/clamp/held/clamp/normal, parser activity and physical MISO data matching, release recovery");$finish;
 end
endmodule

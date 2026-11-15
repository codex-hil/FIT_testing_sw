`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg[1:0]mode=0;wire active,data;
miso_generator dut(clk,mode,active,data);
integer i,edges,last_edge,ticks;reg previous;
initial begin
 repeat(5)@(negedge clk);if(active||data)$fatal(1,"default");
 mode=1;repeat(5)@(negedge clk);if(!active||data)$fatal(1,"low");
 mode=2;repeat(5)@(negedge clk);if(!active||!data)$fatal(1,"high");
 mode=3;repeat(5)@(negedge clk);previous=data;edges=0;last_edge=0;
 for(ticks=0;ticks<100200;ticks=ticks+1)begin
  @(negedge clk);
  if(data!=previous)begin
   if(edges>0&&ticks-last_edge!=20039)$fatal(1,"period");
   last_edge=ticks;edges=edges+1;previous=data;
  end
 end
 if(edges<4)$fatal(1,"edge count");
 mode=1;repeat(5)@(negedge clk);if(!active||data)$fatal(1,"stop low");
 mode=0;repeat(5)@(negedge clk);if(active)$fatal(1,"normal mode");
 $display("PASS: default, static low/high, 20039-tick half-period, stop and normal mode");$finish;
end
endmodule

`timescale 1ns/1ps
module tb;
 reg clk=0,sel=0,mosi=0;reg[2:0]mode=4;
 wire miso;wire[15:0]scratch,writes,shift;wire[5:0]state;wire[7:0]address;
`ifdef WRAPPER
 ab_slave dut(.clk(clk),.sel(sel),.mosi(mosi),.locked(1'b1),.mode(mode),.miso(miso),.scratch_out(scratch),.writes_out(writes),.debug_state(state),.debug_address(address),.debug_shift(shift));
`else
 hdmi_slave dut(.clk(clk),.sel(sel),.mosi(mosi),.locked(1'b1),.miso(miso),.scratch_out(scratch),.writes_out(writes));
`endif
 reg[15:0]rx,before_writes;integer edges;reg old_miso;
 task frame(input read,input[7:0]addr,input[15:0]value);integer i;reg[31:0]packet;begin
 packet=({31'b0,read}<<31)|({24'b0,addr}<<22)|value;rx=0;edges=0;old_miso=miso;sel=1;#3;
 for(i=31;i>=0;i=i-1)begin
  mosi=packet[i];#3;clk=1;#3;
  if(!read&&mode[2]&&miso!==0)$fatal(1,"write MISO not quiet");
  if(i<16)rx={rx[14:0],miso};clk=0;#3;
  if(miso!=old_miso)edges=edges+1;old_miso=miso;
  if(!read&&mode[2]&&miso!==0)$fatal(1,"write falling edge drove MISO");
 end
 sel=0;mosi=0;#3;
 end endtask
 task write_check(input[15:0]value);begin before_writes=writes;frame(0,8'h40,value);if(scratch!==value||writes!==before_writes+16'd1)$fatal(1,"write commit");end endtask
 initial begin
 #3;frame(1,0,0);if(rx!==16'h4844)$fatal(1,"read0");
 write_check(0);write_check(16'hffff);write_check(16'h5555);write_check(16'h0f0f);
 frame(1,1,0);if(rx!==16'h4d49)$fatal(1,"read1");
 frame(1,2,0);if(rx!==1)$fatal(1,"read2");
 frame(1,8'h40,0);if(rx!==16'h0f0f)$fatal(1,"scratch readback");
`ifdef WRAPPER
 mode=0;write_check(16'hffff);if(edges==0)$fatal(1,"raw comparison lost");
 mode=4;write_check(16'h5555);frame(1,0,0);if(rx!==16'h4844)$fatal(1,"release recovery");
`endif
 $display("PASS quiet writes at every sample/edge, exact commits, read0/1/2/scratch, raw comparison where enabled");$finish;
 end
endmodule

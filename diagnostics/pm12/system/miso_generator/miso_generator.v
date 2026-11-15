// 40.0787 MHz / (2*20039) = 1000.017466 Hz. No SYS reset input.
module miso_generator(input clk,input[1:0]mode,
 output active,output data);
 (* ASYNC_REG="TRUE" *)reg[1:0]mode1=0,mode2=0;
 reg[14:0]count=0;reg square=0;
 always @(posedge clk)begin
  mode1<=mode;mode2<=mode1;
  if(mode2!=3)begin count<=0;square<=0;end
  else if(count==20038)begin count<=0;square<=~square;end
  else count<=count+1'b1;
 end
 assign active=(mode2!=0);
 assign data=(mode2==2)?1'b1:(mode2==3)?square:1'b0;
endmodule

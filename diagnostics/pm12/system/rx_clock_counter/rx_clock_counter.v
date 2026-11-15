// Relative clock counts against recovered GTX RXOUTCLK. No SYS reset on state.
module clkr_gray_counter(input clk,output reg[15:0]gray=0);
 reg[15:0]bin=0;wire[15:0]next=bin+16'd1;
 always @(posedge clk)begin bin<=next;gray<=next^(next>>1);end
endmodule
module rx_clock_counter #(parameter WINDOW=384,DEPTH=2048,TIMEOUT=6011805)(
 input ref_clk,mclk,gtref,sys_clk,arm,
 input sys_lock,cap_lock,sys_reset,gt_lock,rx_done,rx_mmcm_lock,
 input[12:0]read_index,input[3:0]csr_index,
 output reg[31:0]csr_data,output[31:0]data);
 wire[15:0]mg,gg,sg;
 clkr_gray_counter c_m(mclk,mg),c_g(gtref,gg),c_s(sys_clk,sg);
 (* ASYNC_REG="TRUE" *)reg[15:0]m1=0,m2=0,g1=0,g2=0,s1=0,s2=0;
 (* ASYNC_REG="TRUE" *)reg[5:0]flags1=0,flags2=0;
 (* ASYNC_REG="TRUE" *)reg arm1=0,arm2=0;
 function[15:0]binary(input[15:0]gray);integer n;begin binary[15]=gray[15];for(n=14;n>=0;n=n-1)binary[n]=binary[n+1]^gray[n];end endfunction
 wire[15:0]mb=binary(m2),gb=binary(g2),sb=binary(s2);
 reg seen=0,active=0,frozen=0,triggered=0,invalid_ref=0;
 reg[4:0]warm=0;reg[31:0]tick=0;reg[15:0]age=0,window_id=0;
 reg[10:0]wp=0;reg[11:0]count=0;
 reg[15:0]mp=0,gp=0,sp=0,min_m=16'hffff,max_m=0,min_g=16'hffff,max_g=0,min_s=16'hffff,max_s=0;
 wire new_arm=arm2!=seen;
 reg sys_loss=0;
 always @(posedge ref_clk or posedge sys_reset)
  if(sys_reset)sys_loss<=1;else if(new_arm)sys_loss<=0;
 wire[15:0]dm=mb-mp,dg=gb-gp,ds=sb-sp;
 wire ref_good=flags2[3]&&flags2[4];
 wire timeout=tick>=TIMEOUT-1;
 wire partial=(age!=WINDOW-1);
 wire[15:0]record_flags={7'b0,invalid_ref,partial,sys_loss,flags2};
 (* ram_style="block" *)reg[127:0]records[0:DEPTH-1];
 always @(posedge ref_clk)begin
  m1<=mg;m2<=m1;g1<=gg;g2<=g1;s1<=sg;s2<=s1;
  flags1<={rx_mmcm_lock,rx_done,gt_lock,sys_reset,cap_lock,sys_lock};flags2<=flags1;
  arm1<=arm;arm2<=arm1;
  if(new_arm)begin
   seen<=arm2;active<=1;frozen<=0;triggered<=0;invalid_ref<=0;warm<=16;
   tick<=0;age<=0;window_id<=0;wp<=0;count<=0;
   min_m<=16'hffff;max_m<=0;min_g<=16'hffff;max_g<=0;min_s<=16'hffff;max_s<=0;
  end else if(active)begin
   tick<=tick+1'b1;
   if(!ref_good)invalid_ref<=1;
   if(warm!=0)begin warm<=warm-1'b1;mp<=mb;gp<=gb;sp<=sb;end
   else if(age==WINDOW-1 || sys_loss || timeout)begin
    records[wp]<={{age+16'd1,window_id},{record_flags,ds},{dg,dm},tick+32'd1};
    wp<=(wp==DEPTH-1)?0:wp+1'b1;if(count<DEPTH)count<=count+1'b1;
    mp<=mb;gp<=gb;sp<=sb;age<=0;window_id<=window_id+1'b1;
    if(ref_good && !partial)begin
     if(dm<min_m)min_m<=dm;if(dm>max_m)max_m<=dm;
     if(dg<min_g)min_g<=dg;if(dg>max_g)max_g<=dg;
     if(ds<min_s)min_s<=ds;if(ds>max_s)max_s<=ds;
    end
    if(sys_loss || timeout)begin active<=0;frozen<=1;triggered<=sys_loss;end
   end else age<=age+1'b1;
  end
 end
 reg[127:0]rd=0;reg[1:0]sel=0;
 always @(posedge sys_clk)begin rd<=records[read_index[12:2]];sel<=read_index[1:0];end
 assign data=(sel==0)?rd[31:0]:(sel==1)?rd[63:32]:(sel==2)?rd[95:64]:rd[127:96];
 // Bundle is sampled, not atomic. Host only downloads after frozen and checks
 // identical count/start/status before and after the complete RAM download.
 wire[31:0]status_ref={25'd0,flags2[4]&&flags2[3],invalid_ref,sys_loss,seen,triggered,frozen,active};
 (* ASYNC_REG="TRUE" *)reg[223:0]status1=0,status2=0;
 always @(posedge sys_clk)begin
  status1<={{min_s,max_s},{min_g,max_g},{min_m,max_m},tick,{4'd0,window_id,count}, {21'd0,wp},status_ref};status2<=status1;
 end
 always @*begin
  case(csr_index)
   0:csr_data=32'h434c4b52;
   1:csr_data=status2[31:0];
   2:csr_data={20'd0,status2[75:64]};
   3:csr_data=(status2[75:64]==DEPTH)?status2[63:32]:0;
   4:csr_data=32'd60118050;
   5:csr_data=WINDOW;
   6:csr_data=status2[127:96];
   7:csr_data={16'd0,status2[91:76]};
   8:csr_data=status2[159:128];
   9:csr_data=status2[191:160];
   10:csr_data=status2[223:192];
   11:csr_data=TIMEOUT;
   12:csr_data=DEPTH;
   default:csr_data=0;
  endcase
 end
endmodule

// Two independent controls: bit0 holds parser reset, bit1 clamps MISO data0.
// The actual HSEL-controlled physical output enable is unchanged in top.
module ab_slave(input clk,sel,mosi,locked,input[1:0]mode,
 output miso,output[15:0]scratch_out,writes_out,
 output[5:0]debug_state,output[7:0]debug_address,output[15:0]debug_shift);
 wire raw_miso;
 hdmi_slave core(.clk(clk),.sel(sel & ~mode[0]),.mosi(mosi),.locked(locked),
 .miso(raw_miso),.scratch_out(scratch_out),.writes_out(writes_out),
 .debug_state(debug_state),.debug_address(debug_address),.debug_shift(debug_shift));
 assign miso=mode[1]?1'b0:raw_miso;
endmodule

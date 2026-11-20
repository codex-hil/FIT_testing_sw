// USER1: DR read, LSB first. USER2: write reset-toggle bit0/freeze bit1.
// Read USER1 only after freeze ack. The top-level adds live pins separately.
module jtag_report (
    input wire tck, reset, capture1, shift1, sel1,
    input wire tck2, reset2, capture2, update2, sel2, shift2, tdi, tdi2,
    input wire [1759:0] report,
    output wire tdo1,
    output reg reset_toggle = 0,
    output reg freeze_request = 0
);
    reg [1759:0] shift_reg = 0;
    reg [1:0] command = 0;
    // USER1 and USER2 have separate BSCANE2 clock outputs. USER2 must not
    // depend on clock activity on the unselected USER1 chain.
    always @(posedge tck) begin
        if (sel1 && capture1) shift_reg <= report;
        else if (sel1 && shift1) shift_reg <= {tdi,shift_reg[1759:1]};
    end
    reg command_shifted = 0;
    always @(posedge tck2) begin
        if (reset2 || (sel2 && capture2)) command_shifted <= 0;
        else if (sel2 && shift2) begin
            command <= {tdi2,command[1]};
            command_shifted <= 1;
        end
    end
    // A TAP reset may expose UPDATE without a fresh payload. Never commit
    // stale command bits while closing the target.
    always @(negedge tck2)
        if (!reset2 && sel2 && update2 && command_shifted) begin
            reset_toggle <= command[0]; freeze_request <= command[1];
        end
    assign tdo1 = shift_reg[0];
endmodule

// ALU for TinyMOA
// Instructions:
// TBD
// https://github.com/MichaelBell/tinyQV/blob/858986b72975157ebf27042779b6caaed164c57b/cpu/alu.v

module tinymoa_alu (
    input [3:0] opcode,
    
    input [3:0] a_in,
    input [3:0] b_in,
    input cmp_in,
    input carry_in,

    output reg [3:0] result,
    output reg cmp_out,
    output carry_out

);
    always @(*) begin
    
    end
endmodule


module tinymoa_multiplier #(parameter B_IN_WIDTH = 16;) (
    input clk

    input [3:0] a_in,
    input [B_IN_WIDTH-1:0] b_in,

    output [3:0] product
);
    reg [B_IN_WIDTH-1:0] accumulator;
    wire [B_IN_WIDTH+3:0] next_accumulator = {4'b0, accumulator} + {{B_IN_WIDTH{1'b0}}, a_in} * {4'd0, b_in};

    always @(posedge clk) begin
        accumulator <= (a_in != 4'b0000) ? next_accumulator[B_IN_WIDTH+3:4] : {4'b0000, accumulator[B_IN_WIDTH-1:4]};
    end

    assign product = next_accumulator[3:0];
endmodule


module tinymoa_shifter (
    input [3:2] opcode,
    
    input [3:0] a_in,
    input [3:0] b_in,
    input [2:0] count_in,


    output reg [3:0] result
);
    // TODO
endmodule

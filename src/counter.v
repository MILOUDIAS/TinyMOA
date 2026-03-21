// Generic counter with variable data width
// Used for program/nibble counter in cpu.v

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_counter #(
    parameter DATA_WIDTH = 32
) (
    input clk,
    input nrst,

    input en,
    input wen,
    input [DATA_WIDTH-1:0] data_in,

    output reg [DATA_WIDTH-1:0] result,
    output c_out
);
    assign c_out = &result;

    always @(posedge clk or negedge nrst) begin
        if (!nrst)
            result <= {DATA_WIDTH{1'b0}};
        else if (wen)
            result <= data_in;
        else if (en)
            result <= result + 1;
    end

endmodule

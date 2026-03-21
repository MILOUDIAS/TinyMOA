// Multiplier test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_multiplier (
    input clk,
    input nrst,

    input [15:0]  a_in,
    input [15:0]  b_in,

    output [31:0] product
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_multiplier.fst");
        $dumpvars(0, tb_multiplier);
        #1;
    end
    `endif

    tinymoa_multiplier dut_multiplier (
        .a_in (a_in),
        .b_in (b_in),
        .product (product)
    );
endmodule

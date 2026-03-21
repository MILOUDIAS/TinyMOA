// Multiplier: 16x16 signed -> 32-bit result
// Core feeds rs1[15:0] and rs2[15:0], then reads product nibble-by-nibble via nibble_ct.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_multiplier (
    input  signed [15:0] a_in,
    input  signed [15:0] b_in,

    output signed [31:0] product
);

    assign product = a_in * b_in;

endmodule

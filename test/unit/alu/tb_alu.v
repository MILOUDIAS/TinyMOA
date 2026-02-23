`default_nettype none
`timescale 1ns / 1ps

module tb_alu (
    input clk,
    input nrst,

    input [3:0] opcode,
    input [31:0] a_in,
    input [31:0] b_in,
    output reg [31:0] result,
    output reg cmp_out
);

    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_alu.fst");
        $dumpvars(0, tb_alu);
        #1;
    end
    `endif

    reg [4:0] nibble_counter = 0;
    wire [4:0] next_counter = nibble_counter + 4;
    always @(posedge clk)
        if (!nrst)
            nibble_counter <= 0;
        else
            nibble_counter <= next_counter;

    reg carry_bit = 0;
    wire carry_in = (nibble_counter == 0) ? (opcode[1] || opcode[3]) : carry_bit;
    wire [3:0] alu_result;
    wire cmp_in = (nibble_counter == 0) ? 1'b1 : cmp_out;
    wire alu_carry_out, alu_cmp_out;
    
    tinymoa_alu alu(
        .opcode(opcode),
        .a_in(a_in[nibble_counter+:4]),
        .b_in(b_in[nibble_counter+:4]),
        .cmp_in(cmp_in),
        .carry_in(carry_in),
        .result(alu_result),
        .cmp_out(alu_cmp_out),
        .carry_out(alu_carry_out)
    );

    always @(posedge clk) begin
        result[nibble_counter+:4] <= alu_result;
        carry_bit <= alu_carry_out;
        cmp_out <= alu_cmp_out;

        if (nibble_counter == 5'b11100)
            if (opcode[2:1] == 2'b01)
                result[0] <= alu_cmp_out;
    end

endmodule

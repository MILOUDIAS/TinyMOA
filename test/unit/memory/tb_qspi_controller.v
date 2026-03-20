`default_nettype none
`timescale 1ns / 1ps

// Testbench for QSPI Controller
// Instantiates qspi_controller and provides interface for cocotb
module tb_qspi_controller (
    input clk,
    input nrst,

    input  [23:0] addr,
    input         read,
    input         write,
    input  [31:0] wdata,
    input  [1:0]  size,

    output [31:0] rdata,
    output        ready,

    output [3:0]  spi_data_in,
    input  [3:0]  spi_data_out,
    input  [3:0]  spi_data_oe,
    input         spi_clk_out,
    input         spi_flash_cs_n,
    input         spi_ram_a_cs_n,
    input         spi_ram_b_cs_n
);

    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_qspi_controller.fst");
        $dumpvars(0, tb_qspi_controller);
        #1;
    end
    `endif

    // Instantiate QSPI controller
    qspi_controller dut (
        .clk            (clk),
        .nrst           (nrst),
        .addr           (addr),
        .read           (read),
        .write          (write),
        .wdata          (wdata),
        .size           (size),
        .rdata          (rdata),
        .ready          (ready),
        .spi_data_in    (spi_data_in),
        .spi_data_out   (spi_data_out),
        .spi_data_oe    (spi_data_oe),
        .spi_clk_out    (spi_clk_out),
        .spi_flash_cs_n (spi_flash_cs_n),
        .spi_ram_a_cs_n (spi_ram_a_cs_n),
        .spi_ram_b_cs_n (spi_ram_b_cs_n)
    );
endmodule

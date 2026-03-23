// TinyMOA integration testbench
//
// Exposes QSPI flash SPI pins so the cocotb test can implement a
// behavioral flash model in Python. Also exposes boot_done and
// cpu_addr for test observability.
//
// SPI pin mapping (matches tinymoa.v uio assignments):
//   spi_flash_cs_n      -> uio_out[3] (output)
//   spi_clk             -> uio_out[0] (output)
//   spi_data_to_flash   -> {uio_out[5],uio_out[4],uio_out[2],uio_out[1]} (output)
//   spi_data_oe         -> {uio_oe[5], uio_oe[4], uio_oe[2], uio_oe[1]}
//   spi_data_from_flash -> drives uio_in[5,4,2,1] (cocotb drives this)

`default_nettype none
`timescale 1ns / 1ps

module tb_tinymoa (
    input clk,
    input nrst,

    input  [3:0]  spi_data_from_flash,
    output [3:0]  spi_data_to_flash,
    output [3:0]  spi_data_oe,
    output        spi_clk,
    output        spi_flash_cs_n,

    output        boot_done,
    output [23:0] cpu_addr
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_tinymoa.fst");
        $dumpvars(0, tb_tinymoa);
        #1;
    end
    `endif

    // Build uio_in from flash SPI data (IO[3:0] -> uio_in[5,4,2,1])
    wire [7:0] uio_in;
    assign uio_in[0] = 1'b0;
    assign uio_in[1] = spi_data_from_flash[0];
    assign uio_in[2] = spi_data_from_flash[1];
    assign uio_in[3] = 1'b0;
    assign uio_in[4] = spi_data_from_flash[2];
    assign uio_in[5] = spi_data_from_flash[3];
    assign uio_in[7:6] = 2'b0;

    wire [7:0] uo_out;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    tinymoa_top dut_tinymoa (
        .clk     (clk),
        .nrst    (nrst),
        .ui_in   (8'b0),
        .uo_out  (uo_out),
        .uio_in  (uio_in),
        .uio_out (uio_out),
        .uio_oe  (uio_oe)
    );

    // Extract SPI outputs from uio
    assign spi_clk           = uio_out[0];
    assign spi_data_to_flash = {uio_out[5], uio_out[4], uio_out[2], uio_out[1]};
    assign spi_data_oe       = {uio_oe[5],  uio_oe[4],  uio_oe[2],  uio_oe[1]};
    assign spi_flash_cs_n    = uio_out[3];

    // Internal signal observation
    assign boot_done = dut_tinymoa.boot_done;
    assign cpu_addr  = dut_tinymoa.cpu_addr;

endmodule

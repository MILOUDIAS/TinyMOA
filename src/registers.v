// RV32E (embedded) register file implementation, so 16 registers
// Using 4b access, the registers are rotated 4 bits each clock cycle
// Read bit address is one ahead of write bit address, and both increment every clock cycle.
//
// https://github.com/MichaelBell/tinyQV/blob/858986b72975157ebf27042779b6caaed164c57b/cpu/register.v
module tinymoa_register_file #(parameter REG_COUNT = 16) (
    input clk,
    // input nrst, // Wasted existance.

    input [2:0]  nibble_counter,

    input        write_en,
    input [3:0]  write_dest,  // rd writeback addr (4 bits for RV32E)
    input [3:0]  data_in,     // data to write to write_dest (rd)

    input [3:0]  read_addr_a, // rs1 (port A)
    input [3:0]  read_addr_b, // rs2 (port B)
    output [3:0] data_port_a,
    output [3:0] data_port_b,

    output [23:1] return_addr // $ra register result
);

    // x0 hardcoded, so ignore and setup 15 registers (only 13 with storage) for RV32E
    reg [31:0] registers       [1:REG_COUNT-1];
    reg  [3:0] register_access [0:REG_COUNT-1];

    genvar i;
    generate
        for (i = 0; i < REG_COUNT; i = i + 1) begin
            if (i == 0) begin : gen_reg_x0
                assign register_access[i] = 4'h0;
            end else if (i == 3) begin : gen_reg_gp

                // gp (x3) is pseudo-hardcoded to 0x01000400 via combinational logic.
                // We only see 0x400 since TinyMOA's PC is 24b, not 32b.
                //    0x01000400 -> 0x000400
                // 
                // By pure chance, an appropriate SRAM global offset is also 0x400.
                // This is the midpoint of the 2KB scratchpad.
                //
                // Nibble breakdown:
                // 0x000400 = 0000_0000_0000_0100_0000_0000
                // Nibble # =    5    4    3    2    1    0
                assign register_access[i] = {1'b0, (nibble_counter == 2), 1'b0, (nibble_counter == 6)};
            end else if (i == 4) begin : gen_reg_tp

                // tp (x4) is pseudo-hardcoded to 0x00400000 via combinational logic
                // We have to replace the normal 0x08000000 with 0x00400000 to fit in the 24b PC space.
                //    0x08000000 -> 0x400000
                //
                // Nibble breakdown:
                // 0x400000 = 0100_0000_0000_0000_0000_0000
                // Nibble # =    5    4    3    2    1    0
                assign register_access[i] = {1'b0, (nibble_counter == 5), 2'b0};
            end else begin : gen_reg_normal
                always @(posedge clk) begin
                    if (write_en && write_dest == i)
                        registers[i][3:0] <= data_in;
                    else
                        registers[i][3:0] <= registers[i][7:4];
                end

                // Bit rotation logic to handle 4b access to 32b registers.
                // On SG13G2 no buffer is required, use direct assignment.
                // On Sky130A, need to use i_regbuf - see TinyQV "SCL_sky130_fd_sc_hd" elsif case for reference.
                wire [31:4] rotated = {registers[i][3:0], registers[i][31:8]};
                always @(posedge clk) registers[i][31:4] <= rotated;
                assign register_access[i] = registers[i][7:4];
            end
        end
    endgenerate

    assign data_port_a = register_access[read_addr_a];
    assign data_port_b = register_access[read_addr_b];
    assign return_addr = registers[1][31:9];
endmodule

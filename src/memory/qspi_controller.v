`default_nettype none
`timescale 1ns / 1ps

// QSPI Controller for TinyMOA
// Consolidates flash and PSRAM access over QSPI/SPI interface.
//
// Supports:
// - Flash: fast read quad I/O (EBh) continuous read mode
// - PSRAM: read (0Bh), write (02h)
//
// Address map:
//   0x000000 - 0x0FFFFF: Flash
//   0x100000 - 0x17FFFF: PSRAM Bank A
//   0x180000 - 0x1FFFFF: PSRAM Bank B

module qspi_controller (
    input wire       clk,
    input wire       nrst,

    input  wire [23:0] addr,       // Address in QSPI space
    input  wire        read,       // Initiate read transaction
    input  wire        write,      // Initiate write transaction
    input  wire [31:0] wdata,      // Write data (32-bit word)
    input  wire [1:0]  size,       // 00=byte, 01=half, 10=word (unused: assume word)
    output reg  [31:0] rdata,      // Read data (32-bit word)
    output reg         ready,      // High when transaction complete

    input  wire [3:0] spi_data_in,
    output reg  [3:0] spi_data_out,
    output reg  [3:0] spi_data_oe,
    output wire       spi_clk_out,
    output reg        spi_flash_cs_n,
    output reg        spi_ram_a_cs_n,
    output reg        spi_ram_b_cs_n
);

    // FSM state definitions
    localparam S_IDLE  = 3'd0;   // Wait for read or write request
    localparam S_CMD   = 3'd1;   // Send command byte (RAM only)
    localparam S_ADDR  = 3'd2;   // Send 24-bit address
    localparam S_DUMMY = 3'd3;   // Send dummy cycles for read latency
    localparam S_DATA  = 3'd4;   // Send or receive data
    localparam S_DONE  = 3'd5;   // Complete transaction, de-assert CS

    // Internal state registers
    reg [2:0]  state;            // Current FSM state
    reg [2:0]  nibble_count;     // Count of nibbles remaining in current phase
    reg [23:0] addr_reg;         // Latched address
    reg [31:0] data_reg;         // Data shift register (read or write)
    reg        is_write;         // Track if current transaction is write
    reg        is_flash_txn;     // Track if current transaction targets flash
    reg [1:0]  size_reg;         // Latched size (unused)
    reg        spi_clk_en;       // SPI clock enable (for clock toggle)

    // Derive data nibble count from size_reg
    // TODO: Properly compute nibbles based on size
    //   size=00 (1B) -> 2 nibbles
    //   size=01 (2B) -> 4 nibbles
    //   size=10 (4B) -> 8 nibbles
    wire [2:0] byte_count   = (size_reg == 2'b00) ? 3'd1 :
                              (size_reg == 2'b01) ? 3'd2 : 3'd4;
    wire [3:0] data_nibbles = {1'b0, byte_count, 1'b0};

    // SPI clock output (toggle at half system clock rate)
    assign spi_clk_out = spi_clk_en;

    // Main FSM (synchronous)
    always @(posedge clk) begin
        if (!nrst) begin
            state          <= S_IDLE;
            ready          <= 1'b0;
            spi_clk_en     <= 1'b0;
            spi_data_oe    <= 4'b0000;
            spi_data_out   <= 4'b1111;
            spi_flash_cs_n <= 1'b1;
            spi_ram_a_cs_n <= 1'b1;
            spi_ram_b_cs_n <= 1'b1;
            rdata          <= 32'd0;
            nibble_count   <= 3'd0;
            is_write       <= 1'b0;
            is_flash_txn   <= 1'b0;
        end else begin
            ready <= 1'b0;

            case (state)
                S_IDLE: begin
                    spi_clk_en <= 1'b0;
                    if (read || write) begin
                        addr_reg     <= addr;
                        data_reg     <= wdata;
                        is_write     <= write;
                        size_reg     <= size;
                        is_flash_txn <= (addr[20] == 1'b0);

                        spi_flash_cs_n <= !(addr[20] == 1'b0);
                        spi_ram_a_cs_n <= !(addr[20:19] == 2'b10);
                        spi_ram_b_cs_n <= !(addr[20:19] == 2'b11);
                        spi_data_oe    <= 4'b1111;

                        if (addr[20] == 1'b0) begin
                            state        <= S_ADDR;
                            nibble_count <= 3'd5;
                        end else begin
                            state        <= S_CMD;
                            nibble_count <= 3'd1;
                        end
                    end
                end

                S_CMD: begin
                    // TODO: Send command byte to PSRAM
                    //   - 0x02 for write, 0x0B for read
                    //   - Toggle spi_clk_en each cycle
                    //   - When nibble_count reaches 0, transition to S_ADDR
                    spi_clk_en <= ~spi_clk_en;
                    if (spi_clk_en) begin
                        if (nibble_count == 0) begin
                            state        <= S_ADDR;
                            nibble_count <= 3'd5;
                        end else
                            nibble_count <= nibble_count - 1;
                    end
                end

                S_ADDR: begin
                    // TODO: Send 24-bit address as 6 nibbles
                    //   - Shift addr_reg left 4 bits per clock
                    //   - Output upper 4 bits to spi_data_out
                    //   - Toggle spi_clk_en each cycle
                    //   - When nibble_count reaches 0:
                    //     * If write (RAM): go to S_DATA
                    //     * If read: go to S_DUMMY (release spi_data_oe)
                    spi_clk_en <= ~spi_clk_en;
                    if (spi_clk_en) begin
                        addr_reg <= {addr_reg[19:0], 4'b0000};
                        if (nibble_count == 0) begin
                            if (is_write && !is_flash_txn) begin
                                state        <= S_DATA;
                                nibble_count <= data_nibbles[2:0] - 1;
                            end else begin
                                state        <= S_DUMMY;
                                nibble_count <= 3'd3; // TODO: tune per device
                                spi_data_oe  <= 4'b0000;
                            end
                        end else
                            nibble_count <= nibble_count - 1;
                    end
                end

                S_DUMMY: begin
                    // TODO: Send dummy nibbles for read latency
                    //   - Dummy nibbles used for timing alignment
                    //   - Toggle spi_clk_en each cycle
                    //   - Count down nibble_count
                    //   - When done, transition to S_DATA, assert spi_data_oe for write
                    spi_clk_en <= ~spi_clk_en;
                    if (spi_clk_en) begin
                        if (nibble_count == 0) begin
                            state        <= S_DATA;
                            nibble_count <= data_nibbles[2:0] - 1;
                            if (is_write)
                                spi_data_oe <= 4'b1111;
                        end else
                            nibble_count <= nibble_count - 1;
                    end
                end

                S_DATA: begin
                    // TODO: Transfer data (read or write)
                    //   - On write: shift data_reg left, output upper 4 bits
                    //   - On read: capture spi_data_in, shift into data_reg
                    //   - Toggle spi_clk_en each cycle
                    //   - When nibble_count reaches 0, transition to S_DONE
                    spi_clk_en <= ~spi_clk_en;
                    if (spi_clk_en) begin
                        if (is_write)
                            data_reg <= {data_reg[27:0], 4'b0000};
                        else
                            data_reg <= {data_reg[27:0], spi_data_in};

                        if (nibble_count == 0)
                            state <= S_DONE;
                        else
                            nibble_count <= nibble_count - 1;
                    end
                end

                S_DONE: begin
                    // TODO: Complete transaction
                    //   - De-assert all CS pins
                    //   - Release data lines (spi_data_oe = 0)
                    //   - Latch read data to rdata
                    //   - Set ready = 1
                    //   - Return to S_IDLE
                    spi_flash_cs_n <= 1'b1;
                    spi_ram_a_cs_n <= 1'b1;
                    spi_ram_b_cs_n <= 1'b1;
                    spi_data_oe    <= 4'b0000;
                    spi_clk_en     <= 1'b0;
                    rdata          <= data_reg;
                    ready          <= 1'b1;
                    state          <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    // SPI data output combinational mux
    // TODO: Generate spi_data_out nibbles based on current state
    //   S_CMD:   0x02 (write) or 0x0B (read) - send 2 nibbles
    //   S_ADDR:  addr_reg[23:20] - 6 nibbles total
    //   S_DATA:  data_reg[31:28] on write, 0xF on read
    //   default: 0xF (high-Z)
    always @(*) begin
        case (state)
            S_CMD:   spi_data_out = is_write ? (!nibble_count[0] ? 4'h2 : 4'h0) :
                                               (!nibble_count[0] ? 4'hB : 4'h0);
            S_ADDR:  spi_data_out = addr_reg[23:20];
            S_DATA:  spi_data_out = is_write ? data_reg[31:28] : 4'hF;
            default: spi_data_out = 4'hF;
        endcase
    end

endmodule
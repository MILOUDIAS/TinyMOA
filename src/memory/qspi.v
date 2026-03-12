`default_nettype none
`timescale 1ns / 1ps

// Flash: fast read quad I/O (EBh) continuous read mode
// PSRAM: read (0Bh), write (02h)
module qspi_controller (
    input wire       clk,
    input wire       rst_n,

    input  wire [23:0] addr,
    input  wire        read,
    input  wire        write,
    input  wire [31:0] wdata,
    input  wire [1:0]  size,  // 00=byte, 01=half, 10=word
    output reg  [31:0] rdata,
    output reg         ready,

    input  wire [3:0] spi_data_in,
    output reg  [3:0] spi_data_out,
    output reg  [3:0] spi_data_oe,
    output wire       spi_clk_out,
    output reg        spi_flash_cs_n,
    output reg        spi_ram_a_cs_n,
    output reg        spi_ram_b_cs_n
);

    localparam S_IDLE  = 3'd0;
    localparam S_CMD   = 3'd1;
    localparam S_ADDR  = 3'd2;
    localparam S_DUMMY = 3'd3;
    localparam S_DATA  = 3'd4;
    localparam S_DONE  = 3'd5;

    reg [2:0]  state;
    reg [2:0]  nibble_count;
    reg [23:0] addr_reg;
    reg [31:0] data_reg;
    reg        is_write;
    reg        is_flash_txn;
    reg [1:0]  size_reg;
    reg        spi_clk_en;

    wire [2:0] byte_count   = (size_reg == 2'b00) ? 3'd1 :
                              (size_reg == 2'b01) ? 3'd2 : 3'd4;
    wire [3:0] data_nibbles = {1'b0, byte_count, 1'b0};

    assign spi_clk_out = spi_clk_en;

    always @(posedge clk) begin
        if (!rst_n) begin
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
                        is_flash_txn <= (addr[23:22] == 2'b00);

                        spi_flash_cs_n <= !(addr[23:22] == 2'b00);
                        spi_ram_a_cs_n <= !(addr[23:22] == 2'b10);
                        spi_ram_b_cs_n <= !(addr[23:22] == 2'b11);
                        spi_data_oe    <= 4'b1111;

                        // Flash skips CMD (continuous read), PSRAM sends CMD first
                        if (addr[23:22] == 2'b00) begin
                            state        <= S_ADDR;
                            nibble_count <= 3'd5;
                        end else begin
                            state        <= S_CMD;
                            nibble_count <= 3'd1;
                        end
                    end
                end

                S_CMD: begin
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

    // SPI data output mux
    always @(*) begin
        case (state)
            S_CMD:   spi_data_out = is_write ? (nibble_count[0] ? 4'h0 : 4'h2) :
                                               (nibble_count[0] ? 4'h0 : 4'hB);
            S_ADDR:  spi_data_out = addr_reg[23:20];
            S_DATA:  spi_data_out = is_write ? data_reg[31:28] : 4'hF;
            default: spi_data_out = 4'hF;
        endcase
    end

endmodule
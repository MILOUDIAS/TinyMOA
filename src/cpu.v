// TinyMOA CPU Core
// FSM: FETCH -> DECODE -> EXECUTE -> MEM (loads/stores only) -> WB

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_cpu (
    input  clk,
    input  nrst,

    // Unified memory interface
    input             mem_ready,
    output reg [23:0] mem_addr,
    output reg        mem_read,
    output reg        mem_write,
    output     [1:0]  mem_size,    // 00=byte, 01=half, 10=word
    output     [31:0] mem_wdata,
    input      [31:0] mem_rdata
);

    // === State registers ===
    reg [2:0]  cpu_state;
    reg [31:0] cpu_instr;     // latched from mem_rdata  in DECODE
    reg [31:0] cpu_execute;   // latched from alu_result in EXECUTE
    reg [31:0] cpu_writeback; // latched from mem_rdata  in MEM


    // === Program Counter ===
    reg         pc_en;
    reg         pc_wen;
    reg  [3:0]  pc_inc;
    reg  [23:0] pc_next;
    wire [23:0] cpu_pc;
    wire        pc_overflow;

    tinymoa_counter #(.DATA_WIDTH(24)) pc (
        .clk     (clk),
        .nrst    (nrst),
        .en      (pc_en),
        .wen     (pc_wen),
        .inc     (pc_inc),
        .data_in (pc_next),
        .result  (cpu_pc),
        .c_out   (pc_overflow)
    );


    // === Decoder ===
    wire [31:0] decoder_imm;
    wire [3:0]  decoder_alu_opcode;
    wire [2:0]  decoder_mem_opcode;
    wire [3:0]  decoder_rs1;
    wire [3:0]  decoder_rs2;
    wire [3:0]  decoder_rd;
    wire        decoder_is_load;
    wire        decoder_is_store;
    wire        decoder_is_branch;
    wire        decoder_is_jal;
    wire        decoder_is_jalr;
    wire        decoder_is_lui;
    wire        decoder_is_auipc;
    wire        decoder_is_alu_reg;
    wire        decoder_is_alu_imm;
    wire        decoder_is_system;
    wire        decoder_is_compressed;

    tinymoa_decoder decoder (
        .instr         (cpu_instr),
        .imm           (decoder_imm),
        .alu_opcode    (decoder_alu_opcode),
        .mem_opcode    (decoder_mem_opcode),
        .rs1           (decoder_rs1),
        .rs2           (decoder_rs2),
        .rd            (decoder_rd),
        .is_load       (decoder_is_load),
        .is_store      (decoder_is_store),
        .is_branch     (decoder_is_branch),
        .is_jal        (decoder_is_jal),
        .is_jalr       (decoder_is_jalr),
        .is_lui        (decoder_is_lui),
        .is_auipc      (decoder_is_auipc),
        .is_alu_reg    (decoder_is_alu_reg),
        .is_alu_imm    (decoder_is_alu_imm),
        .is_system     (decoder_is_system),
        .is_compressed (decoder_is_compressed)
    );


    // === Register file ===
    wire [31:0] regfile_rs1_data;
    wire [31:0] regfile_rs2_data;
    reg  [31:0] regfile_rd_data;
    reg         regfile_rd_wen;

    tinymoa_registers registers (
        .clk      (clk),
        .nrst     (nrst),
        .rs1_sel  (decoder_rs1),
        .rs1_data (regfile_rs1_data),
        .rs2_sel  (decoder_rs2),
        .rs2_data (regfile_rs2_data),
        .rd_wen   (regfile_rd_wen),
        .rd_sel   (decoder_rd),
        .rd_data  (regfile_rd_data)
    );


    // === ALU ===
    reg  [31:0] alu_a_in;
    reg  [31:0] alu_b_in;
    wire [31:0] alu_result;

    // Defaults to rs1+imm (covers I/S/B/load/store address)
    always @(*) begin
        alu_a_in = regfile_rs1_data;
        alu_b_in = decoder_imm;
        if (decoder_is_alu_reg) alu_b_in = regfile_rs2_data;
        if (decoder_is_branch)  alu_b_in = regfile_rs2_data;
        if (decoder_is_auipc)   alu_a_in = {8'b0, cpu_pc};
    end

    tinymoa_alu alu (
        .opcode (decoder_alu_opcode),
        .a_in   (alu_a_in),
        .b_in   (alu_b_in),
        .result (alu_result)
    );
    

    // Load sign/zero extension from cpu_writeback
    reg [31:0] load_ext;
    always @(*) begin
        case (decoder_mem_opcode)
            3'b000:  load_ext = {{24{cpu_writeback[7]}},  cpu_writeback[7:0]};  // LB
            3'b100:  load_ext = {24'b0,                   cpu_writeback[7:0]};  // LBU
            3'b001:  load_ext = {{16{cpu_writeback[15]}}, cpu_writeback[15:0]}; // LH
            3'b101:  load_ext = {16'b0,                   cpu_writeback[15:0]}; // LHU
            default: load_ext = cpu_writeback;                                  // LW
        endcase
    end


    // === Memory interface ===
    assign mem_wdata = regfile_rs2_data;
    assign mem_size  = decoder_mem_opcode[1:0];

    wire [23:0] link_addr = cpu_pc + (decoder_is_compressed ? 24'd2 : 24'd4);

    // === FSM ===
    localparam FSM_FETCH   = 3'd0;
    localparam FSM_DECODE  = 3'd1;
    localparam FSM_EXECUTE = 3'd2;
    localparam FSM_MEM     = 3'd3;
    localparam FSM_WB      = 3'd4;

    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            cpu_state       <= FSM_FETCH;
            cpu_instr       <= 32'b0;
            cpu_execute     <= 32'b0;
            cpu_writeback   <= 32'b0;
            mem_addr        <= 24'd0;
            mem_read        <= 1'b0;
            mem_write       <= 1'b0;
            regfile_rd_wen  <= 1'b0;
            regfile_rd_data <= 32'b0;
            pc_en           <= 1'b0;
            pc_wen          <= 1'b0;
            pc_inc          <= 4'd0;
            pc_next         <= 24'd0;
        end else begin
            regfile_rd_wen <= 1'b0;
            pc_en          <= 1'b0;
            pc_wen         <= 1'b0;

            case (cpu_state)

                // FETCH: present cpu_pc to memory, assert mem_read.
                // Wait here until mem_ready. TCM=1 cycle, QSPI=N cycles.
                // When mem_ready: mem_rdata is valid -- latch into cpu_instr, go to EXECUTE.
                FSM_FETCH: begin

                end
                FSM_DECODE: begin
                    // mem_rdata now valid. Latch instruction; decoder sees it next cycle.
                    mem_read   <= 1'b0;
                    cpu_instr  <= mem_rdata;
                    cpu_state  <= FSM_EXECUTE;
                end
                // EXECUTE: cpu_instr is stable, all decoder outputs are combinational.
                // ALU result is combinational from alu_a_in/alu_b_in.
                // Latch alu_result into cpu_execute.
                // Load or store -> go to MEM. Everything else -> go to WB.
                
                FSM_EXECUTE: begin

                end

                // MEM: present cpu_execute[23:0] as the effective address.
                // Load  -> assert mem_read,  wait for mem_ready, latch mem_rdata into cpu_writeback.
                // Store -> assert mem_write, wait for mem_ready (write completes, no latch needed).
                // Then go to WB.
                FSM_MEM: begin

                end

                // WB: select writeback value and write to rd.
                //   Skip write if rd=x0, is_store, or is_branch.
                //   ALU/AUIPC  -> cpu_execute
                //   Load       -> load_ext (sign/zero extended cpu_writeback)
                //   LUI        -> decoder_imm
                //   JAL/JALR   -> link_addr (cpu_pc + 2 or +4)
                // Update PC:
                //   Normal           -> cpu_pc + 2 or +4
                //   JAL              -> cpu_pc + decoder_imm[23:0]
                //   JALR             -> cpu_execute[23:0] & 24'hFFFFFE
                //   Branch taken     -> cpu_pc + decoder_imm[23:0]
                //   Branch not taken -> cpu_pc + 2 or +4
                FSM_WB: begin

                    cpu_state <= FSM_FETCH;
                end

                default: cpu_state <= FSM_FETCH;
            endcase
        end
    end

    wire _unused = &{decoder_is_system, decoder_is_alu_imm, decoder_is_branch,
                     decoder_is_auipc, 1'b0};

endmodule

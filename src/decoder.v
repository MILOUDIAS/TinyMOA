// TinyMOA Combinational Instruction Decoder
//
// Decodes RV32I, C/Zca, Zcb, and Zicond from a 32-bit word.
// 16-bit compressed instructions arrive zero-extended to 32 bits.
//
// Compressed register fields (3-bit) map to x8-x15: rd = {1'b1, instr[N:M]}.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_decoder (
    input [31:0] instr,

    output reg  [31:0] imm,
    output reg  [3:0]  alu_opcode,
    output reg  [2:0]  mem_opcode, // [1:0]=size, [2]=unsigned
    output reg  [3:0]  rs1,
    output reg  [3:0]  rs2,
    output reg  [3:0]  rd,

    output reg         is_load,
    output reg         is_store,
    output reg         is_branch,
    output reg         is_jal,
    output reg         is_jalr,
    output reg         is_lui,
    output reg         is_auipc,
    output reg         is_alu_reg,
    output reg         is_alu_imm,
    output reg         is_system,
    output reg         is_compressed
);

    // Hardcoded bit-fields to prevent slicing mistakes.

    // R-Type instructions:
    // [31:25] funct7
    // [24:20] rs2
    // [19:15] rs1
    // [14:12] funct3
    // [11:7]  rd
    // [6:0]   opcode

    // I-Type instructions:
    // [31:20] imm[11:0]
    // [19:15] rs1
    // [14:12] funct3
    // [11:7]  rd
    // [6:0]   opcode

    // S-Type instructions:
    // [31:25] imm[11:5]
    // [24:20] rs2
    // [19:15] rs1
    // [14:12] funct3
    // [11:7]  imm[4:0]
    // [6:0]   opcode

    // B-Type instructions:
    // [31]    imm[12]
    // [30:25] imm[10:5]
    // [24:20] rs2
    // [19:15] rs1
    // [14:12] funct3
    // [11:8]  imm[4:1]
    // [7]     imm[11]
    // [6:0]   opcode

    // U-Type instructions:
    // [31:11] imm[31:12]
    // [11:7]  rd
    // [6:0]   opcode

    // J-Type instructions:
    // [31]    imm[20]
    // [30:21] imm[10:1]
    // [20]    imm[11]
    // [19:12] imm[19:12]
    // [11:7]  rd
    // [6:0]   opcode

    // RV32C Compressed ISA

    // CR-Type instructions:
    // [15:12] funct4 (opcode)
    // [11:7]  rs2'/rd'
    // [6:2]   rs2
    // [1:0]   op (quadrant)

    // CI-Type instructions:
    // [15:13] funct3 (opcode)
    // [12]    imm[5]
    // [11:7]  rs1'/rd'
    // [6:2]   imm[6:2]
    // [1:0]   op (quadrant)

    // CSS-Type instructions:
    // [15:13] funct3 (opcode)
    // [12:7]  imm[12:7]
    // [6:2]   imm[6:2]
    // [1:0]   op (quadrant)

    // CIW-Type instructions:
    // [15:13] funct3 (opcode)
    // [12:7]  imm[17:12]
    // [6:2]   imm[11:7]
    // [1:0]   op (quadrant)
    
    // CL-Type instructions:
    // [15:13] funct3 (opcode)
    // [12:10] imm[12:10] (hi)
    // [9:7]   rs1'
    // [6:5]   imm[6:5] (lo)
    // [4:2]   rd'
    // [1:0]   op (quadrant)

    // CS-Type instructions:
    // [15:13] funct3 (opcode)
    // [12:10] imm[12:10] (hi)
    // [9:7]   rs1'
    // [6:5]   imm[6:5] (lo)
    // [4:2]   rs2'
    // [1:0]   op (quadrant)

    // CA-Type instructions:
    // [15:10] funct6 (opcode)
    // [9:7]   rd'/rs1'
    // [6:5]   imm
    // [4:2]   rs2'
    // [1:0]   op (quadrant)

    // CB-Type instructions:
    // [15:13] funct3 (opcode)
    // [12:10] offset (hi)
    // [9:7]   rd'/rs1'
    // [6:2]   offset (lo)
    // [1:0]   op (quadrant)

    // CJ-Type instructions:
    // [15:13] funct3 (opcode)
    // [12:2]  target address
    // [1:0] op (quadrant)

    wire [1:0] quadrant = instr[1:0];
    wire [4:0] i_opcode = instr[6:2];   // bits[1:0] == 2'b11 for all 32-bit instructions
    wire [2:0] c_funct3 = instr[15:13]; // compressed major opcode

    wire [2:0] funct3   = instr[14:12];
    wire [6:0] funct7   = instr[31:25];

    // 32-bit register fields (RV32E: 4-bit, x0-x15)
    wire [3:0] rs1_32 = instr[18:15];
    wire [3:0] rs2_32 = instr[23:20];
    wire [3:0] rd_32  = instr[10:7];

    // Compressed prime register fields: 3-bit encoding maps to x8-x15 ({1'b1, field})
    wire [3:0] c_rs1p = {1'b1, instr[9:7]};
    wire [3:0] c_rs2p = {1'b1, instr[4:2]};
    wire [3:0] c_rdp  = {1'b1, instr[4:2]};

    // Compressed full register fields (non-prime, used in CI/CR/CSS types)
    wire [3:0] c_rs1 = instr[10:7];
    wire [3:0] c_rs2 = instr[6:2];  // NOTE: upper bit ignored for RV32E (x0-x15 only)
    wire [3:0] c_rd  = instr[10:7];

    always @(*) begin
        imm           = 32'd0;
        alu_opcode    = 4'd0;
        mem_opcode    = 3'd0;
        rs1           = 4'd0;
        rs2           = 4'd0;
        rd            = 4'd0;
        is_load       = 1'b0;
        is_store      = 1'b0;
        is_branch     = 1'b0;
        is_jal        = 1'b0;
        is_jalr       = 1'b0;
        is_lui        = 1'b0;
        is_auipc      = 1'b0;
        is_alu_reg    = 1'b0;
        is_alu_imm    = 1'b0;
        is_system     = 1'b0;
        is_compressed = 1'b0;

        // === RV32I 32-bit instructions ===
        if (quadrant == 2'b11) begin
            rs1 = rs1_32;
            rs2 = rs2_32;
            rd  = rd_32;

            case (i_opcode)

                // === R-Type: Register-register and Zicond ===
                5'b01100: begin
                    is_alu_reg = 1'b1;

                    // Zicond: funct7=0000111, funct3=101 (EQZ) or 110 (NEZ)
                    if (funct7 == 7'b0000111) begin
                        alu_opcode = {3'b111, funct3[1]}; // CZERO.EQZ=1110, CZERO.NEZ=1111

                    // Standard ALU operations
                    end else begin
                        case (funct3)
                            3'b000: alu_opcode = funct7[5] ? 4'b0001 : 4'b0000; // SUB : ADD
                            3'b001: alu_opcode = 4'b1000;                        // SLL
                            3'b010: alu_opcode = 4'b0010;                        // SLT
                            3'b011: alu_opcode = 4'b0011;                        // SLTU
                            3'b100: alu_opcode = 4'b0100;                        // XOR
                            3'b101: alu_opcode = funct7[5] ? 4'b1010 : 4'b1001; // SRA : SRL
                            3'b110: alu_opcode = 4'b0101;                        // OR
                            3'b111: alu_opcode = 4'b0110;                        // AND
                        endcase
                    end
                end

                // === I-Type: ALU immediate ===
                // imm[11:0] = instr[31:20], sign-extended
                // Shifts: shamt = imm[4:0] = instr[24:20], SRAI/SRLI via instr[30]
                5'b00100: begin
                    is_alu_imm = 1'b1;
                    imm = {{20{instr[31]}}, instr[31:20]};
                    case (funct3)
                        3'b000: alu_opcode = 4'b0000;                             // ADDI
                        3'b001: alu_opcode = 4'b1000;                             // SLLI
                        3'b010: alu_opcode = 4'b0010;                             // SLTI
                        3'b011: alu_opcode = 4'b0011;                             // SLTIU
                        3'b100: alu_opcode = 4'b0100;                             // XORI
                        3'b101: alu_opcode = instr[30] ? 4'b1010 : 4'b1001;      // SRAI : SRLI
                        3'b110: alu_opcode = 4'b0101;                             // ORI
                        3'b111: alu_opcode = 4'b0110;                             // ANDI
                    endcase
                end

                // === I-Type: Load ===
                // imm[11:0] = instr[31:20], sign-extended
                // funct3: LB=000, LH=001, LW=010, LBU=100, LHU=101
                // mem_opcode[1:0]=size (00=byte,01=half,10=word), [2]=unsigned
                5'b00000: begin
                    is_load    = 1'b1;
                    imm        = {{20{instr[31]}}, instr[31:20]};
                    mem_opcode = {funct3[2], funct3[1:0]};
                end

                // === I-Type: JALR ===
                // funct3=000, target = (rs1 + sign-ext imm) & ~1
                5'b11001: begin
                    is_jalr = 1'b1;
                    imm     = {{20{instr[31]}}, instr[31:20]};
                end

                // === S-Type instructions ===
                5'b01000: begin
                    is_store = 1'b1;
                end

                // === B-Type instructions ===
                5'b11000: begin
                    is_branch = 1'b1;
                end

                // === U-Type instructions ===
                5'b00101: begin // AUIPC only
                    is_auipc = 1'b1;
                end

                // === U-Type instructions ===
                5'b01101: begin // LUI only
                    is_lui = 1'b1;
                end

                // === J-Type instructions ===
                5'b11011: begin // JAL only
                    is_jal = 1'b1;
                end

                // === SYSTEM instructions ===
                5'b11100: begin
                    is_system = 1'b1;
                end

                // FENCE: NOP
                5'b00011: begin end
            endcase

        // === RV32C 16-bit compressed instructions ===
        end else begin
            is_compressed = 1'b1;

            case (quadrant)

                // === Quadrant 0 ===
                2'b00: begin
                    case (c_funct3)

                    endcase
                end

                // === Quadrant 1 ===
                2'b01: begin
                    case (c_funct3)

                    endcase
                end

                // === Quadrant 2 ===
                2'b10: begin
                    case (c_funct3)

                    endcase
                end

                default: begin end
            endcase
        end
    end
endmodule

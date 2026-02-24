"""Instruction encoders for RV32EC (RV32E + C extension)

Manual encoding without external dependencies.
Provides clean, testable instruction encoders.
"""

# ============================================================================
# BASE ENCODING FUNCTIONS
# ============================================================================


def encode_r_type(funct7, rs2, rs1, funct3, rd, opcode):
    """Encode R-type: funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]"""
    return (
        (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
    )


def encode_i_type(imm, rs1, funct3, rd, opcode):
    """Encode I-type: imm[31:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]"""
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def encode_s_type(imm, rs2, rs1, funct3, opcode):
    """Encode S-type: imm[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | imm[11:7] | opcode[6:0]"""
    return (
        (((imm >> 5) & 0x7F) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | ((imm & 0x1F) << 7)
        | opcode
    )


def encode_b_type(imm, rs2, rs1, funct3, opcode):
    """Encode B-type: imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode"""
    return (
        (((imm >> 12) & 1) << 31)
        | (((imm >> 5) & 0x3F) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (((imm >> 1) & 0xF) << 8)
        | (((imm >> 11) & 1) << 7)
        | opcode
    )


def encode_u_type(imm, rd, opcode):
    """Encode U-type: imm[31:12] | rd[11:7] | opcode[6:0]"""
    return ((imm & 0xFFFFF) << 12) | (rd << 7) | opcode


def encode_j_type(imm, rd, opcode):
    """Encode J-type: imm[20|10:1|11|19:12] | rd | opcode"""
    return (
        (((imm >> 20) & 1) << 31)
        | (((imm >> 1) & 0x3FF) << 21)
        | (((imm >> 11) & 1) << 20)
        | (((imm >> 12) & 0xFF) << 12)
        | (rd << 7)
        | opcode
    )


# ============================================================================
# RV32E BASE INSTRUCTIONS (32-bit)
# ============================================================================

# --- R-Type ALU Operations ---


def encode_add(rd, rs1, rs2):
    """ADD rd, rs1, rs2 - Add"""
    return encode_r_type(0x00, rs2, rs1, 0x0, rd, 0x33)


def encode_sub(rd, rs1, rs2):
    """SUB rd, rs1, rs2 - Subtract"""
    return encode_r_type(0x20, rs2, rs1, 0x0, rd, 0x33)


def encode_and(rd, rs1, rs2):
    """AND rd, rs1, rs2 - Bitwise AND"""
    return encode_r_type(0x00, rs2, rs1, 0x7, rd, 0x33)


def encode_or(rd, rs1, rs2):
    """OR rd, rs1, rs2 - Bitwise OR"""
    return encode_r_type(0x00, rs2, rs1, 0x6, rd, 0x33)


def encode_xor(rd, rs1, rs2):
    """XOR rd, rs1, rs2 - Bitwise XOR"""
    return encode_r_type(0x00, rs2, rs1, 0x4, rd, 0x33)


def encode_sll(rd, rs1, rs2):
    """SLL rd, rs1, rs2 - Shift Left Logical"""
    return encode_r_type(0x00, rs2, rs1, 0x1, rd, 0x33)


def encode_srl(rd, rs1, rs2):
    """SRL rd, rs1, rs2 - Shift Right Logical"""
    return encode_r_type(0x00, rs2, rs1, 0x5, rd, 0x33)


def encode_sra(rd, rs1, rs2):
    """SRA rd, rs1, rs2 - Shift Right Arithmetic"""
    return encode_r_type(0x20, rs2, rs1, 0x5, rd, 0x33)


def encode_slt(rd, rs1, rs2):
    """SLT rd, rs1, rs2 - Set Less Than"""
    return encode_r_type(0x00, rs2, rs1, 0x2, rd, 0x33)


def encode_sltu(rd, rs1, rs2):
    """SLTU rd, rs1, rs2 - Set Less Than Unsigned"""
    return encode_r_type(0x00, rs2, rs1, 0x3, rd, 0x33)


# --- I-Type ALU Operations ---


def encode_addi(rd, rs1, imm):
    """ADDI rd, rs1, imm - Add Immediate"""
    return encode_i_type(imm, rs1, 0x0, rd, 0x13)


def encode_andi(rd, rs1, imm):
    """ANDI rd, rs1, imm - AND Immediate"""
    return encode_i_type(imm, rs1, 0x7, rd, 0x13)


def encode_ori(rd, rs1, imm):
    """ORI rd, rs1, imm - OR Immediate"""
    return encode_i_type(imm, rs1, 0x6, rd, 0x13)


def encode_xori(rd, rs1, imm):
    """XORI rd, rs1, imm - XOR Immediate"""
    return encode_i_type(imm, rs1, 0x4, rd, 0x13)


def encode_slti(rd, rs1, imm):
    """SLTI rd, rs1, imm - Set Less Than Immediate"""
    return encode_i_type(imm, rs1, 0x2, rd, 0x13)


def encode_sltiu(rd, rs1, imm):
    """SLTIU rd, rs1, imm - Set Less Than Immediate Unsigned"""
    return encode_i_type(imm, rs1, 0x3, rd, 0x13)


def encode_slli(rd, rs1, shamt):
    """SLLI rd, rs1, shamt - Shift Left Logical Immediate"""
    return encode_i_type(shamt & 0x1F, rs1, 0x1, rd, 0x13)


def encode_srli(rd, rs1, shamt):
    """SRLI rd, rs1, shamt - Shift Right Logical Immediate"""
    return encode_i_type(shamt & 0x1F, rs1, 0x5, rd, 0x13)


def encode_srai(rd, rs1, shamt):
    """SRAI rd, rs1, shamt - Shift Right Arithmetic Immediate"""
    return encode_i_type(0x400 | (shamt & 0x1F), rs1, 0x5, rd, 0x13)


# --- Load Operations ---


def encode_lw(rd, rs1, imm):
    """LW rd, imm(rs1) - Load Word"""
    return encode_i_type(imm, rs1, 0x2, rd, 0x03)


def encode_lh(rd, rs1, imm):
    """LH rd, imm(rs1) - Load Halfword"""
    return encode_i_type(imm, rs1, 0x1, rd, 0x03)


def encode_lb(rd, rs1, imm):
    """LB rd, imm(rs1) - Load Byte"""
    return encode_i_type(imm, rs1, 0x0, rd, 0x03)


def encode_lbu(rd, rs1, imm):
    """LBU rd, imm(rs1) - Load Byte Unsigned"""
    return encode_i_type(imm, rs1, 0x4, rd, 0x03)


def encode_lhu(rd, rs1, imm):
    """LHU rd, imm(rs1) - Load Halfword Unsigned"""
    return encode_i_type(imm, rs1, 0x5, rd, 0x03)


# --- Store Operations ---


def encode_sw(rs1, rs2, imm):
    """SW rs2, imm(rs1) - Store Word"""
    return encode_s_type(imm, rs2, rs1, 0x2, 0x23)


def encode_sh(rs1, rs2, imm):
    """SH rs2, imm(rs1) - Store Halfword"""
    return encode_s_type(imm, rs2, rs1, 0x1, 0x23)


def encode_sb(rs1, rs2, imm):
    """SB rs2, imm(rs1) - Store Byte"""
    return encode_s_type(imm, rs2, rs1, 0x0, 0x23)


# --- Branch Operations ---


def encode_beq(rs1, rs2, imm):
    """BEQ rs1, rs2, offset - Branch if Equal"""
    return encode_b_type(imm, rs2, rs1, 0x0, 0x63)


def encode_bne(rs1, rs2, imm):
    """BNE rs1, rs2, offset - Branch if Not Equal"""
    return encode_b_type(imm, rs2, rs1, 0x1, 0x63)


def encode_blt(rs1, rs2, imm):
    """BLT rs1, rs2, offset - Branch if Less Than"""
    return encode_b_type(imm, rs2, rs1, 0x4, 0x63)


def encode_bge(rs1, rs2, imm):
    """BGE rs1, rs2, offset - Branch if Greater or Equal"""
    return encode_b_type(imm, rs2, rs1, 0x5, 0x63)


def encode_bltu(rs1, rs2, imm):
    """BLTU rs1, rs2, offset - Branch if Less Than Unsigned"""
    return encode_b_type(imm, rs2, rs1, 0x6, 0x63)


def encode_bgeu(rs1, rs2, imm):
    """BGEU rs1, rs2, offset - Branch if Greater or Equal Unsigned"""
    return encode_b_type(imm, rs2, rs1, 0x7, 0x63)


# --- Jump Operations ---


def encode_jal(rd, imm):
    """JAL rd, offset - Jump and Link"""
    return encode_j_type(imm, rd, 0x6F)


def encode_jalr(rd, rs1, imm):
    """JALR rd, rs1, offset - Jump and Link Register"""
    return encode_i_type(imm, rs1, 0x0, rd, 0x67)


# --- Upper Immediate Operations ---


def encode_lui(rd, imm):
    """LUI rd, imm - Load Upper Immediate"""
    return encode_u_type(imm, rd, 0x37)


def encode_auipc(rd, imm):
    """AUIPC rd, imm - Add Upper Immediate to PC"""
    return encode_u_type(imm, rd, 0x17)


# --- System Operations ---


def encode_ecall():
    """ECALL - Environment Call"""
    return 0x73


def encode_ebreak():
    """EBREAK - Environment Break"""
    return 0x00100073


# ============================================================================
# RV32C COMPRESSED INSTRUCTIONS (16-bit)
# ============================================================================


def encode_c_add(rd, rs2):
    """C.ADD rd, rs2 - Compressed Add"""
    return 0x9002 | (rd << 7) | (rs2 << 2)


def encode_c_mv(rd, rs2):
    """C.MV rd, rs2 - Compressed Move"""
    return 0x8002 | (rd << 7) | (rs2 << 2)


def encode_c_li(rd, imm):
    """C.LI rd, imm - Compressed Load Immediate"""
    scrambled = ((imm & 0x20) << 7) | ((imm & 0x1F) << 2)
    return 0x4001 | scrambled | (rd << 7)


def encode_c_addi(rd, imm):
    """C.ADDI rd, imm - Compressed Add Immediate"""
    scrambled = ((imm & 0x20) << 7) | ((imm & 0x1F) << 2)
    return 0x0001 | scrambled | (rd << 7)


def encode_c_lw(rd, rs1, imm):
    """C.LW rd, imm(rs1) - Compressed Load Word (rd, rs1 must be x8-x15)"""
    scrambled = ((imm & 0x38) << 7) | ((imm & 0x04) << 4) | ((imm & 0x40) >> 1)
    return 0x4000 | scrambled | ((rs1 & 0x7) << 7) | ((rd & 0x7) << 2)


def encode_c_sw(rs1, rs2, imm):
    """C.SW rs2, imm(rs1) - Compressed Store Word (rs1, rs2 must be x8-x15)"""
    scrambled = ((imm & 0x38) << 7) | ((imm & 0x04) << 4) | ((imm & 0x40) >> 1)
    return 0xC000 | scrambled | ((rs1 & 0x7) << 7) | ((rs2 & 0x7) << 2)


def encode_c_j(imm):
    """C.J offset - Compressed Jump"""
    scrambled = (
        ((imm & 0x800) << 1)
        | ((imm & 0x010) << 7)
        | ((imm & 0x300) << 1)
        | ((imm & 0x400) >> 2)
        | ((imm & 0x040) << 1)
        | ((imm & 0x080) >> 1)
        | ((imm & 0x00E) << 2)
        | ((imm & 0x020) >> 3)
    )
    return 0xA001 | scrambled


def encode_c_beqz(rs1, imm):
    """C.BEQZ rs1, offset - Compressed Branch if Equal to Zero (rs1 must be x8-x15)"""
    scrambled = (
        ((imm & 0x100) << 4)
        | ((imm & 0x0C0) << 4)
        | ((imm & 0x018) >> 2)
        | ((imm & 0x006) << 2)
        | ((imm & 0x020) >> 3)
    )
    return 0xC001 | scrambled | ((rs1 & 0x7) << 7)


def encode_c_bnez(rs1, imm):
    """C.BNEZ rs1, offset - Compressed Branch if Not Equal to Zero (rs1 must be x8-x15)"""
    scrambled = (
        ((imm & 0x100) << 4)
        | ((imm & 0x0C0) << 4)
        | ((imm & 0x018) >> 2)
        | ((imm & 0x006) << 2)
        | ((imm & 0x020) >> 3)
    )
    return 0xE001 | scrambled | ((rs1 & 0x7) << 7)

"""
Test suite for decoding RV32I instructions

Loads (LB, LH, LW, LBU, LHU):
- load_byte_signed
- load_halfword_signed
- load_word
- load_byte_unsigned
- load_halfword_unsigned
- load_immediate_sign_extension
- load_register_fields

Stores (SB, SH, SW):
- store_byte
- store_halfword
- store_word
- store_immediate_reconstruction
- store_register_fields

ALU immediate (ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI):
- addi_basic
- addi_immediate_min_max
- slti_sltiu
- xori_ori_andi
- slli_srli_srai_opcode
- srai_vs_srli_funct7

ALU reg-reg (ADD, SUB, SLL, SRL, SRA, AND, OR, XOR, SLT, SLTU):
- add_sub_funct7_distinguishes
- shift_opcodes
- logical_opcodes
- slt_sltu_opcodes

Zicond (CZERO.EQZ, CZERO.NEZ):
- czero_eqz_opcode
- czero_nez_opcode

Branches (BEQ, BNE, BLT, BGE, BLTU, BGEU):
- branch_all_types
- branch_immediate_sign_extension
- branch_immediate_max_min

Jumps:
- jal_immediate_encoding
- jal_rd_zero
- jalr_immediate_and_rs1

Upper immediate:
- lui_immediate_lower_zeros
- auipc_immediate_lower_zeros

System / other:
- fence_is_nop
- ecall_ebreak_is_system
- all_zeros_instruction
- bits_not_11_routes_to_compressed
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup_tb_decoder_rv32i(dut):
    """Initialize the decoder for RV32I operations"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def test_foo(dut):
    """Test template"""
    await setup_tb_decoder_rv32i(dut)
    await ClockCycles(dut.clk, 1)

    raise NotImplementedError("Test not implemented yet")

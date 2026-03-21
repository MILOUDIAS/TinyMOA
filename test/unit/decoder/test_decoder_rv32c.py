"""
Test suite for decoding RV32C (Zca, Zcb) instructions

Quadrant 0:
- caddi4spn_rd_and_sp_as_rs1
- clw_load_fields
- csw_store_fields
- zcb_byte_halfword_load_store

Quadrant 1:
- cnop
- caddi_rd_rs1_immediate
- cjal_rd_is_ra
- cli_rs1_is_x0
- clui_is_lui
- caddi16sp_immediate_scale
- csrli_opcode
- csrai_opcode
- candi_opcode
- csub_cxor_cor_cand_opcodes
- cj_rd_is_x0
- cbeqz_branch_and_xor_opcode
- cbnez_branch_and_xor_opcode

Quadrant 2:
- cslli_opcode
- clwsp_sp_as_rs1
- cjr_rs1_rd_x0
- cmv_is_alu_reg
- cadd_rd_rs1_same
- cjalr_rd_is_ra
- cmul_nonstandard_opcode
- cswsp_sp_as_rs1

Register encoding:
- prime_register_decode_x8_to_x15
- full_register_decode_x0_to_x15

is_compressed flag:
- compressed_flag_set_for_all_q0_q1_q2
- compressed_flag_clear_for_32bit
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup_tb_decoder_rv32c(dut):
    """Initialize the decoder for RV32EC operations"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def test_foo(dut):
    """Test template"""
    await setup_tb_decoder_rv32c(dut)
    await ClockCycles(dut.clk, 1)

    raise NotImplementedError("Test not implemented yet")

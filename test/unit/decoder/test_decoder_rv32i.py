"""
Test suite for decoding RV32I instructions.

Every test verifies ALL control lines: imm, alu_opcode, mem_opcode, rs1, rs2, rd,
the correct is_* flag high, all others low, and is_compressed=0.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
import utility.rv32i_encode as rv32i


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def decode(dut, instr_val):
    dut.instr.value = instr_val
    await Timer(1, unit="ns")


# === R-Type ===


@cocotb.test()
async def test_add(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_sub(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_sll(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_slt(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_sltu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_xor(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_srl(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_sra(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_or(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_and(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_czero_eqz(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_czero_nez(dut):
    await setup(dut)
    raise NotImplementedError


# === I-Type ===


@cocotb.test()
async def test_addi(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_slti(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_sltiu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_xori(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_ori(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_andi(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_slli(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_srli(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_srai(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_lb(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_lh(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_lw(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_lbu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_lhu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_jalr(dut):
    await setup(dut)
    raise NotImplementedError


# === S-Type ===


@cocotb.test()
async def test_sb(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_sh(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_sw(dut):
    await setup(dut)
    raise NotImplementedError


# === B-Type ===


@cocotb.test()
async def test_beq(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_bne(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_blt(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_bge(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_bltu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_bgeu(dut):
    await setup(dut)
    raise NotImplementedError


# === U-Type ===


@cocotb.test()
async def test_lui(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_auipc(dut):
    await setup(dut)
    raise NotImplementedError


# === J-Type ===


@cocotb.test()
async def test_jal(dut):
    await setup(dut)
    raise NotImplementedError

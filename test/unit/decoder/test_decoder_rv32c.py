"""
Test suite for decoding RV32C (Zca, Zcb) instructions.

Every test verifies ALL control lines: is_compressed=1, the correct is_* flag high,
all others low, rs1/rs2/rd (prime register decode where applicable), imm bit layout,
alu_opcode, mem_opcode.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
import utility.rv32c_encode as rv32c


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def decode(dut, instr_val):
    dut.instr.value = instr_val
    await Timer(1, unit="ns")


# === Quadrant 0 ===


# CIW-Type
@cocotb.test()
async def test_c_addi4spn(dut):
    await setup(dut)
    raise NotImplementedError


# CL
@cocotb.test()
async def test_c_lw(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_lbu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_lhu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_lh(dut):
    await setup(dut)
    raise NotImplementedError


# CS
@cocotb.test()
async def test_c_sw(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_sb(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_sh(dut):
    await setup(dut)
    raise NotImplementedError


# === Quadrant 1 ===


# CI
@cocotb.test()
async def test_c_nop(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_addi(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_li(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_addi16sp(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_lui(dut):
    await setup(dut)
    raise NotImplementedError


# CA
@cocotb.test()
async def test_c_sub(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_xor(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_or(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_and(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_mul(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_not(dut):
    await setup(dut)
    raise NotImplementedError


# CB
@cocotb.test()
async def test_c_srli(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_srai(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_andi(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_beqz(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_bnez(dut):
    await setup(dut)
    raise NotImplementedError


# CJ
@cocotb.test()
async def test_c_j(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_jal(dut):
    await setup(dut)
    raise NotImplementedError


# === Quadrant 2 ===


# CR
@cocotb.test()
async def test_c_jr(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_mv(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_jalr(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_add(dut):
    await setup(dut)
    raise NotImplementedError


# CI
@cocotb.test()
async def test_c_slli(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_lwsp(dut):
    await setup(dut)
    raise NotImplementedError


# CSS
@cocotb.test()
async def test_c_swsp(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_c_swtp(dut):
    await setup(dut)
    raise NotImplementedError

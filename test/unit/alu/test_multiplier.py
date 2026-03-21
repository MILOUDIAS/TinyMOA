"""
Test suite for the ALU (tinymoa_multiplier)
- positive_times_positive
- negative_times_positive
- negative_times_negative
- zero_times_n
- max_times_max
- min_times_min
- product_nibble_extraction
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    dut.opcode.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.c_in.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def run_alu_op(dut, opcode, a, b, c=0, iterations=150):
    """Run ALU operation over many random inputs."""
    dut.opcode.value = int(opcode)
    dut.a_in.value = int(a)
    dut.b_in.value = int(b)
    dut.c_in.value = int(c)
    await ClockCycles(dut.clk, 1)
    results = []
    for _ in range(iterations):
        await ClockCycles(dut.clk, 7)
        next_a = random.randint(0, 0xFFFFFFFF)
        next_b = random.randint(0, 0xFFFFFFFF)
        dut.a_in.value = int(next_a)
        dut.b_in.value = int(next_b)
        await ClockCycles(dut.clk, 1)
        results.append((int(dut.result.value), a, b))
        a, b = next_a, next_b
    return results


@cocotb.test()
async def positive_times_positive(dut):
    """Test multiply positive * positive"""
    await setup(dut)
    a = random.randint(0, 0xFFFFFFFF)
    b = random.randint(0, 0xFFFFFFFF)
    for result, a_val, b_val in await run_alu_op(dut, 0b0000, a, b):
        expected = (a_val * b_val) & 0xFFFFFFFF
        assert result == expected, (
            f"{a_val} * {b_val}: expected {expected}, got {result}"
        )

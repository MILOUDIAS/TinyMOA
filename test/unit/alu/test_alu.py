import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from numpy import random


async def setup_alu(alu, opcode):
    clock = Clock(alu.clk, 4, units="ns")
    cocotb.start_soon(clock.start())

    alu.opcode.value = opcode

    alu.nrst.value = 0
    alu.a_in.value = 0
    alu.b_in.value = 0
    await ClockCycles(alu.clk, 1)
    alu.nrst.value = 1

    return alu


async def test_alu_operation(alu, operation, iterations=150):
    a = random.randint(0, 0xFFFFFFFF)
    b = random.randint(0, 0xFFFFFFFF)
    alu.a_in.value = int(a)
    alu.b_in.value = int(b)
    await ClockCycles(alu.clk, 1)

    for _ in range(iterations):
        await ClockCycles(alu.clk, 7)
        expected = int(operation(a, b) & 0xFFFFFFFF)

        # Load new values for the next operation
        a = random.randint(0, 0xFFFFFFFF)
        b = random.randint(0, 0xFFFFFFFF)
        alu.a_in.value = int(a)
        alu.b_in.value = int(b)
        await ClockCycles(alu.clk, 1)

        # Result is READY on the 8th cycle but needs the final nibble to be loaded
        # The result is fully VIEWABLE on the 9th cycle
        # Save yourselves the massive headache.
        result = alu.result.value
        assert result == expected, f"Expected {expected}, got {result}"


async def test_alu_comparison(alu, comparison, value_gen, iterations=100):
    a, b = value_gen()
    alu.a_in.value = int(a)
    alu.b_in.value = int(b)
    await ClockCycles(alu.clk, 1)

    for _ in range(iterations):
        await ClockCycles(alu.clk, 7)
        expected = 1 if comparison(a, b) else 0

        # Load new values for the next comparison
        a, b = value_gen()
        alu.a_in.value = int(a)
        alu.b_in.value = int(b)
        await ClockCycles(alu.clk, 1)

        assert alu.cmp_out.value == expected


@cocotb.test()
async def test_add(alu):
    await setup_alu(alu, 0b0000)
    await test_alu_operation(alu, lambda a, b: a + b)


@cocotb.test()
async def test_sub(alu):
    await setup_alu(alu, 0b1000)
    await test_alu_operation(alu, lambda a, b: a - b)


@cocotb.test()
async def test_and(alu):
    await setup_alu(alu, 0b0111)
    await test_alu_operation(alu, lambda a, b: a & b)


@cocotb.test()
async def test_or(alu):
    await setup_alu(alu, 0b0110)
    await test_alu_operation(alu, lambda a, b: a | b)


@cocotb.test()
async def test_xor(alu):
    await setup_alu(alu, 0b0100)  # Note: Same opcode as EQ
    await test_alu_operation(alu, lambda a, b: a ^ b)


@cocotb.test()
async def test_eq(alu):
    await setup_alu(alu, 0b0100)  # Note: Same opcode as XOR

    def gen_values():
        a = random.randint(0, 0xFFFFFFFF)
        temp = random.randint(0, 0xFFFFFFFF)
        b = random.choice((a, temp))
        return a, b

    await test_alu_comparison(alu, lambda a, b: a == b, gen_values)


@cocotb.test()
async def test_slt(alu):
    await setup_alu(alu, 0b0010)

    def gen_values():
        a = random.randint(-0x80000000, 0x7FFFFFFF)
        b = random.randint(-0x80000000, 0x7FFFFFFF)
        return a, b

    await test_alu_comparison(alu, lambda a, b: a < b, gen_values)


@cocotb.test()
async def test_sltu(alu):
    await setup_alu(alu, 0b0011)

    def gen_values():
        a = random.randint(0, 0xFFFFFFFF)
        b = random.randint(0, 0xFFFFFFFF)
        return a, b

    await test_alu_comparison(alu, lambda a, b: a < b, gen_values)

"""Test suite for QSPI PSRAM"""

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


FLASH_START = 0x000000
FLASH_END = 0x0FFFFF
PSRAM_A_START = 0x100000
PSRAM_A_END = 0x17FFFF
PSRAM_B_START = 0x180000
PSRAM_B_END = 0x1FFFFF


async def setup_qspi(dut):
    """Initialize QSPI controller with clock and reset."""
    clock = Clock(dut.clk, 4, unit="ns")
    cocotb.start_soon(clock.start())

    dut.nrst.value = 0
    dut.read.value = 0
    dut.write.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    dut.size.value = 0b10
    dut.spi_data_in.value = 0

    await ClockCycles(dut.clk, 2)
    dut.nrst.value = 1
    await ClockCycles(dut.clk, 1)


async def wait_for_ready(dut, timeout=1000):
    """Wait until ready signal is high."""
    cycles = 0
    while cycles < timeout:
        if int(dut.ready.value) == 1:
            return cycles
        await RisingEdge(dut.clk)
        cycles += 1
    raise AssertionError(f"QSPI did not assert ready within {timeout} cycles")


async def do_qspi_read(dut, addr, expected_data=None):
    """Initiate a QSPI read and simulate SPI slave response."""
    data_word = expected_data if expected_data is not None else 0xDEADBEEF

    # Pre-set first nibble before transaction starts
    first_nibble = (data_word >> 28) & 0xF
    dut.spi_data_in.value = first_nibble

    dut.read.value = 1
    dut.addr.value = addr
    await RisingEdge(dut.clk)
    dut.read.value = 0

    prev_clk = 0
    oe_clk_count = 0

    for _ in range(500):
        if int(dut.ready.value) == 1:
            return int(dut.rdata.value)

        curr_oe = int(dut.spi_data_oe.value)
        curr_clk = int(dut.spi_clk_out.value)

        if curr_clk == 1 and prev_clk == 0 and curr_oe == 0:
            oe_clk_count += 1
            if oe_clk_count >= 4 and oe_clk_count < 12:
                data_idx = oe_clk_count - 4
                nibble = (data_word >> (28 - data_idx * 4)) & 0xF
                dut.spi_data_in.value = nibble

        prev_clk = curr_clk
        await RisingEdge(dut.clk)

    raise AssertionError("QSPI read timed out")


async def do_qspi_write(dut, addr, write_data):
    """Initiate a QSPI write transaction."""
    dut.write.value = 1
    dut.addr.value = addr
    dut.wdata.value = write_data
    await RisingEdge(dut.clk)
    dut.write.value = 0

    cycles = await wait_for_ready(dut)
    return cycles


@cocotb.test()
async def test_psram_a_write(dut):
    """PSRAM A write with randomized addresses and data"""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(PSRAM_A_START, PSRAM_A_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        cycles = await do_qspi_write(dut, addr, int(data))
        assert cycles > 0


@cocotb.test()
async def test_psram_a_cs_timing(dut):
    """PSRAM A CS should be asserted during transaction."""
    await setup_qspi(dut)

    for _ in range(10):
        addr = np.random.randint(PSRAM_A_START, PSRAM_A_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        dut.write.value = 1
        dut.addr.value = addr
        dut.wdata.value = int(data)
        await RisingEdge(dut.clk)
        dut.write.value = 0

        await RisingEdge(dut.clk)
        assert int(dut.spi_ram_a_cs_n.value) == 0

        await wait_for_ready(dut)
        assert int(dut.spi_ram_a_cs_n.value) == 1


@cocotb.test()
async def test_psram_a_write_command(dut):
    """PSRAM A write should send 0x02 command."""
    await setup_qspi(dut)

    for _ in range(10):
        addr = np.random.randint(PSRAM_A_START, PSRAM_A_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        dut.write.value = 1
        dut.addr.value = addr
        dut.wdata.value = int(data)
        await RisingEdge(dut.clk)
        dut.write.value = 0

        first_nibble_high = None
        first_nibble_low = None

        for _ in range(100):
            if int(dut.ready.value) == 1:
                break

            prev_clk = int(dut.spi_clk_out.value)
            await RisingEdge(dut.clk)
            curr_clk = int(dut.spi_clk_out.value)

            if prev_clk == 0 and curr_clk == 1:
                if first_nibble_high is None:
                    first_nibble_high = int(dut.spi_data_out.value)
                elif first_nibble_low is None:
                    first_nibble_low = int(dut.spi_data_out.value)

        assert first_nibble_high == 0x0
        assert first_nibble_low == 0x2


@cocotb.test()
async def test_psram_b_write(dut):
    """PSRAM B write with randomized addresses and data"""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(PSRAM_B_START, PSRAM_B_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        cycles = await do_qspi_write(dut, addr, int(data))
        assert cycles > 0


@cocotb.test()
async def test_psram_b_cs_timing(dut):
    """PSRAM B CS should be asserted during transaction."""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(PSRAM_B_START, PSRAM_B_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        dut.write.value = 1
        dut.addr.value = addr
        dut.wdata.value = int(data)
        await RisingEdge(dut.clk)
        dut.write.value = 0

        await RisingEdge(dut.clk)
        assert int(dut.spi_ram_b_cs_n.value) == 0

        await wait_for_ready(dut)
        assert int(dut.spi_ram_b_cs_n.value) == 1


@cocotb.test()
async def test_psram_read(dut):
    """PSRAM read with randomized addresses and data"""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(PSRAM_A_START, PSRAM_B_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        rdata = await do_qspi_read(dut, addr, int(data))
        assert rdata == int(data)


@cocotb.test()
async def test_psram_read_command(dut):
    """PSRAM read should send 0x0B command."""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(PSRAM_A_START, PSRAM_B_END + 1)

        dut.read.value = 1
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        dut.read.value = 0

        first_nibble_high = None
        first_nibble_low = None

        for i in range(100):
            if int(dut.ready.value) == 1:
                break

            prev_clk = int(dut.spi_clk_out.value)
            await RisingEdge(dut.clk)
            curr_clk = int(dut.spi_clk_out.value)

            if prev_clk == 0 and curr_clk == 1:
                data_out = int(dut.spi_data_out.value)
                if first_nibble_high is None:
                    first_nibble_high = data_out
                    print(
                        f"[test_psram_read_command] First nibble at iter {i}: 0x{data_out:x}"
                    )
                elif first_nibble_low is None:
                    first_nibble_low = data_out
                    print(
                        f"[test_psram_read_command] Second nibble at iter {i}: 0x{data_out:x}"
                    )
                    break

        print(
            f"[test_psram_read_command] Read command bytes: 0x{first_nibble_high:x}{first_nibble_low:x}"
        )
        assert first_nibble_high == 0x0, (
            f"Expected high nibble 0x0, got 0x{first_nibble_high:x}"
        )
        assert first_nibble_low == 0xB, (
            f"Expected low nibble 0xB, got 0x{first_nibble_low:x}"
        )

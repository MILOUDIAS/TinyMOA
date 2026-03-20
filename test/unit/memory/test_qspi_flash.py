"""Test suite for QSPI flash"""

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
async def test_reset_idle(dut):
    """After reset, all outputs should be inactive."""
    await setup_qspi(dut)

    assert int(dut.spi_flash_cs_n.value) == 1
    assert int(dut.spi_ram_a_cs_n.value) == 1
    assert int(dut.spi_ram_b_cs_n.value) == 1
    assert int(dut.spi_clk_out.value) == 0
    assert int(dut.spi_data_oe.value) == 0
    assert int(dut.ready.value) == 0


@cocotb.test()
async def test_idle_no_clock_toggle(dut):
    """Module should remain idle until read or write request."""
    await setup_qspi(dut)

    for _ in range(10):
        assert int(dut.spi_clk_out.value) == 0
        assert int(dut.spi_flash_cs_n.value) == 1
        await RisingEdge(dut.clk)


@cocotb.test()
async def test_flash_read(dut):
    """Flash read with randomized addresses and data."""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(FLASH_START, FLASH_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        rdata = await do_qspi_read(dut, addr, int(data))
        assert rdata == int(data)


@cocotb.test()
async def test_flash_cs_timing(dut):
    """Flash CS should be asserted during transaction."""
    await setup_qspi(dut)

    for _ in range(10):
        addr = np.random.randint(FLASH_START, FLASH_END + 1)

        dut.read.value = 1
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        dut.read.value = 0

        await RisingEdge(dut.clk)
        assert int(dut.spi_flash_cs_n.value) == 0

        await wait_for_ready(dut)
        assert int(dut.spi_flash_cs_n.value) == 1

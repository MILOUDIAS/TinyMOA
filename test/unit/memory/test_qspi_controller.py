"""Test suite for the QSPI controller"""

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
    """Wait until ready signal pulses high then low."""
    cycles = 0
    saw_ready = False
    while cycles < timeout:
        if int(dut.ready.value) == 1:
            saw_ready = True
        elif saw_ready and int(dut.ready.value) == 0:
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
async def test_spi_clock_toggle(dut):
    """SPI clock should toggle during transactions"""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(FLASH_START, FLASH_END + 1)

        dut.read.value = 1
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        dut.read.value = 0

        await RisingEdge(dut.clk)

        toggles = 0
        for _ in range(200):
            if int(dut.ready.value) == 1:
                break

            prev_clk = int(dut.spi_clk_out.value)
            await RisingEdge(dut.clk)
            curr_clk = int(dut.spi_clk_out.value)

            if prev_clk != curr_clk:
                toggles += 1

        assert toggles >= 17


@cocotb.test()
async def test_data_oe_control(dut):
    """spi_data_oe should be driven during write, released during read"""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(PSRAM_A_START, PSRAM_A_END + 1)
        data = np.random.randint(0, 0x100000000, dtype=np.uint32)

        dut.write.value = 1
        dut.addr.value = addr
        dut.wdata.value = int(data)
        await RisingEdge(dut.clk)
        dut.write.value = 0

        oe_high = False
        for _ in range(300):
            if int(dut.ready.value) == 1:
                break

            if int(dut.spi_data_oe.value) != 0:
                oe_high = True

            await RisingEdge(dut.clk)

        assert oe_high

    for _ in range(50):
        addr = np.random.randint(PSRAM_A_START, PSRAM_A_END + 1)

        dut.read.value = 1
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        dut.read.value = 0

        oe_released = False
        for i in range(500):
            if int(dut.ready.value) == 1:
                break

            if i > 20 and int(dut.spi_data_oe.value) == 0:
                oe_released = True

            await RisingEdge(dut.clk)

        assert oe_released


@cocotb.test()
async def test_ready_signal_timing(dut):
    """Ready signal should pulse high for one cycle"""
    await setup_qspi(dut)

    for _ in range(50):
        addr = np.random.randint(FLASH_START, FLASH_END + 1)

        dut.read.value = 1
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        dut.read.value = 0

        ready_seen = False
        for _ in range(1000):
            await RisingEdge(dut.clk)

            if int(dut.ready.value) == 1:
                ready_seen = True
                await RisingEdge(dut.clk)
                assert int(dut.ready.value) == 0
                break

        assert ready_seen


@cocotb.test()
async def test_sequential_operations(dut):
    """Back-to-back read/write operations"""
    await setup_qspi(dut)

    for _ in range(50):
        flash_addr = np.random.randint(FLASH_START, FLASH_END + 1)
        psram_addr = np.random.randint(PSRAM_A_START, PSRAM_B_END + 1)
        data1 = np.random.randint(0, 0x100000000, dtype=np.uint32)
        data2 = np.random.randint(0, 0x100000000, dtype=np.uint32)

        await do_qspi_read(dut, flash_addr, int(data1))
        await do_qspi_write(dut, psram_addr, int(data2))


@cocotb.test()
async def test_cs_isolation(dut):
    """CS pins should not glitch when switching devices"""
    await setup_qspi(dut)

    for _ in range(50):
        flash_addr = np.random.randint(FLASH_START, FLASH_END + 1)
        psram_addr = np.random.randint(PSRAM_A_START, PSRAM_B_END + 1)

        dut.read.value = 1
        dut.addr.value = flash_addr
        await RisingEdge(dut.clk)
        dut.read.value = 0

        await wait_for_ready(dut)

        assert int(dut.spi_flash_cs_n.value) == 1
        assert int(dut.spi_ram_a_cs_n.value) == 1
        assert int(dut.spi_ram_b_cs_n.value) == 1

        dut.write.value = 1
        dut.addr.value = psram_addr
        dut.wdata.value = 0xDEADBEEF
        await RisingEdge(dut.clk)
        dut.write.value = 0

        await ClockCycles(dut.clk, 3)

        if psram_addr < PSRAM_B_START:
            assert int(dut.spi_ram_a_cs_n.value) == 0
        else:
            assert int(dut.spi_ram_b_cs_n.value) == 0

        assert int(dut.spi_flash_cs_n.value) == 1

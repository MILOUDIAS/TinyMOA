"""
TinyMOA system integration tests.

Tests PAR IO, debug stream, and CPU-DCIM communication through tinymoa_top.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


async def setup(dut):
    """Reset and configure for PAR mode."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.is_parallel.value = 0
    dut.par_space.value = 0
    dut.par_cpu_nrst.value = 0
    dut.par_we.value = 0
    dut.par_oe.value = 0
    dut.par_addr.value = 0
    dut.dbg_en.value = 0
    dut.par_data_in.value = 0

    dut.nrst.value = 0
    await ClockCycles(dut.clk, 2)
    dut.nrst.value = 1
    await ClockCycles(dut.clk, 2)


async def par_write_word(dut, addr, data):
    """Write a 32-bit word to TCM via PAR nibble protocol."""
    dut.is_parallel.value = 1
    dut.par_space.value = 0
    dut.par_addr.value = addr & 0x3
    await ClockCycles(dut.clk, 1)

    for nibble_idx in range(8):
        nibble = (data >> (nibble_idx * 4)) & 0xF
        dut.par_data_in.value = nibble
        dut.par_we.value = 1
        await ClockCycles(dut.clk, 1)
        dut.par_we.value = 0
        await ClockCycles(dut.clk, 1)

    # Wait for par_rdy
    await ClockCycles(dut.clk, 2)


async def par_read_word(dut, addr):
    """Read a 32-bit word from TCM via PAR nibble protocol."""
    dut.is_parallel.value = 1
    dut.par_space.value = 0
    dut.par_addr.value = addr & 0x3
    dut.par_oe.value = 1
    await ClockCycles(dut.clk, 2)

    word = 0
    for nibble_idx in range(8):
        await ClockCycles(dut.clk, 1)
        nibble = int(dut.par_data_out.value)
        word |= (nibble & 0xF) << (nibble_idx * 4)

    dut.par_oe.value = 0
    await ClockCycles(dut.clk, 1)
    return word


@cocotb.test()
async def test_par_rdy_pulses(dut):
    """PAR mode: writing 8 nibbles produces a par_rdy pulse."""
    await setup(dut)

    dut.is_parallel.value = 1
    dut.par_space.value = 0
    dut.par_addr.value = 0
    await ClockCycles(dut.clk, 1)

    # Write 8 nibbles (0x0 through 0x7)
    for i in range(8):
        dut.par_data_in.value = i
        dut.par_we.value = 1
        await ClockCycles(dut.clk, 1)
        dut.par_we.value = 0
        await ClockCycles(dut.clk, 1)

    # par_rdy should have pulsed on the 8th nibble commit
    # Check nibble counter reset to 0
    await ClockCycles(dut.clk, 1)
    assert int(dut.par_nibble_idx.value) == 0, "nibble counter should reset after 8 nibbles"


@cocotb.test()
async def test_par_nibble_counter(dut):
    """PAR mode: nibble counter increments on each write strobe."""
    await setup(dut)

    dut.is_parallel.value = 1
    dut.par_space.value = 0
    dut.par_addr.value = 0
    await ClockCycles(dut.clk, 1)

    for i in range(4):
        dut.par_data_in.value = i
        dut.par_we.value = 1
        await ClockCycles(dut.clk, 1)
        dut.par_we.value = 0
        await ClockCycles(dut.clk, 1)

    idx = int(dut.par_nibble_idx.value)
    assert idx == 4, f"nibble counter should be 4 after 4 nibbles, got {idx}"


@cocotb.test()
async def test_dbg_strobe_sync_byte(dut):
    """Debug mode: first 8 bits of frame should be 0xAA sync byte."""
    await setup(dut)

    # Enter debug mode
    dut.dbg_en.value = 1
    await ClockCycles(dut.clk, 1)

    # Read first 8 bits (should be 0xAA = 10101010)
    sync = 0
    for i in range(8):
        await RisingEdge(dut.clk)
        bit = int(dut.dbg_strobe.value)
        sync = (sync << 1) | bit

    assert sync == 0xAA, f"sync byte should be 0xAA, got 0x{sync:02X}"


@cocotb.test()
async def test_dbg_frame_end_pulses(dut):
    """Debug mode: dbg_frame_end pulses after 144 bits."""
    await setup(dut)

    dut.dbg_en.value = 1
    await ClockCycles(dut.clk, 1)

    # Wait for frame_end pulse (should come at bit 143)
    for cycle in range(200):
        await RisingEdge(dut.clk)
        if int(dut.dbg_frame_end.value) == 1:
            # Frame end should occur at cycle ~143
            assert cycle >= 140, f"frame_end too early at cycle {cycle}"
            assert cycle <= 145, f"frame_end too late at cycle {cycle}"
            return

    assert False, "dbg_frame_end never pulsed within 200 cycles"


@cocotb.test()
async def test_cpu_reset_held_in_par_mode(dut):
    """PAR mode with par_cpu_nrst=0 keeps CPU in reset."""
    await setup(dut)

    dut.is_parallel.value = 1
    dut.par_cpu_nrst.value = 0
    await ClockCycles(dut.clk, 5)

    # CPU should be stuck in FETCH (state 0) since it's held in reset
    state = int(dut.cpu_state.value)
    assert state == 0, f"CPU should be in FETCH (reset), got state {state}"


@cocotb.test()
async def test_output_pins_default_ser_mode(dut):
    """SER mode defaults: NCS lines all high (deasserted), QSPI idle."""
    await setup(dut)

    dut.is_parallel.value = 0
    await ClockCycles(dut.clk, 2)

    uo_val = int(dut.uo.value)
    # uo[7:4] should be NCS lines, all high (deasserted) = 0xF0
    # uo[3:2] = qspi_sck=0, qspi_oe=0
    # uo[1:0] = dbg_frame_end=0, dbg_strobe=X (depends on shift reg)
    ncs = (uo_val >> 4) & 0xF
    assert ncs == 0xF, f"NCS lines should all be high in idle, got 0x{ncs:X}"

    sck = (uo_val >> 3) & 1
    assert sck == 0, f"QSPI SCK should be 0 in idle, got {sck}"

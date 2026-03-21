"""
Test suite for the ALU (tinymoa_alu, tinymoa_shifter, tinymoa_multiplier)

tinymoa_alu:
- add_basic
- add_carry_propagation
- add_overflow_wrap
- sub_basic
- sub_borrow_propagation
- sub_negative_result
- and_basic
- or_basic
- xor_basic
- bitwise_all_zeros
- bitwise_all_ones
- slt_positive_less_than
- slt_negative_less_than
- slt_equal
- sltu_unsigned_compare
- czero_eqz
- czero_nez
- carry_chain_across_nibbles
- cmp_out_accumulation_across_nibbles

tinymoa_shifter:
- sll_by_zero
- sll_by_one
- sll_by_sixteen
- sll_by_thirtyone
- srl_by_one
- srl_by_sixteen
- srl_by_thirtyone
- sra_positive_by_one
- sra_negative_by_one
- sra_negative_by_thirtyone
- nibble_extraction_all_positions

tinymoa_multiplier:
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


async def setup_tb_alu(dut):
    """Initialize the ALU"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def test_foo(dut):
    """Test template"""
    await setup_tb_alu(dut)
    await ClockCycles(dut.clk, 1)

    raise NotImplementedError("Test not implemented yet")

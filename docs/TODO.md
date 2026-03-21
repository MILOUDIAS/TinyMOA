# TinyMOA ABC TODO

Target: functional RV32EC CPU on Alchitry Cu V2 (iCE40UP5K, behavioral TCM), then DCIM accelerator.

North star: Architecture.md, ISA.md, Bootloader.md, DCIM.md.

---

## Done

- [x] Finalize address map and DCIM array size (32x32, IHP 130nm)
- [x] Write all module skeletons (`tinymoa.v`, `cpu.v`, `decoder.v`, `alu.v`, `registers.v`, `counter.v`, `tcm.v`, `bootloader.v`, `qspi.v`, `dcim.v`)
- [x] Write all testbench skeletons (`tb_*.v`, `test_*.py` with test lists)
- [x] Fix signal naming across all modules (CPU bus: `mem_read/write/rdata/wdata`, bootloader: `rom_read`, `tcm_wdata`)
- [x] Fix syntax errors (`tb_counter.v`, `bootloader.v`)
- [x] TCM behavioral model (`ifdef BEHAVIORAL` path complete)
- [x] Counter module (complete, parameterized)
- [x] DCIM MMIO register read/write block (complete in `dcim.v`)
- [x] DCIM documentation rewrite (DCIM.md: compressor circuit, MB-XNOR format, CPU interface, C pseudo-code, OpenLane hardening, performance estimates)
- [x] Create `tinymoa_compressor` module (`src/dcim/compressor.v`: double-approx + exact via ifdef)
- [x] Fix dcim.v default addresses (0x1A0/0x1C0/0x1E0), bit-plane processing order (MSB-first descending), STORE_RESULT/FETCH_ACT comments
- [x] Move DCIM files to `src/dcim/` directory (`dcim.v`, `compressor.v`)
- [x] Fix `registers.v:54`: `rd_wr_en` → `rd_wen`
- [x] Fix `alu.v` case statement: added `4'b1000` (SUB), `4'b0010`/`4'b0011` (SLT/SLTU result=0), `4'b1110`/`4'b1111` (CZERO pass-through; CPU FSM handles condition)
- [x] Fix `Architecture.md` module hierarchy: `sram.v` → `tcm.v`, `boot.v` → `bootloader.v`; fix wrong default address constants in TCM layout note (`0x1A0/0x1C0/0x1E0`)
- [x] Add single-approximate compressor mode (`SINGLE_APPROX_COMPRESSOR` ifdef in `compressor.v`): level-1 AND/OR, then exact 8-bit popcount; output range 0-8; ~40% fewer transistors, RMSE ≈ 4.03%
- [x] Implement DCIM FSM state bodies (`dcim.v`): pipelined LOAD_WEIGHTS (N+1 cycles), FETCH_ACT (2-cycle with fetch_wait), COMPUTE (shift-accumulate), STORE_RESULT (signed conversion: `2*acc - bias`), DONE
- [x] Instantiate 2x `tinymoa_compressor` per column in generate block, sum → `popcount[col]`
- [x] Hardware signed conversion: `bias_reg` computed in IDLE, `store_signed = 2*shift_acc[col] - bias_reg`, sign-extended to 32-bit in STORE_RESULT
- [x] **`registers.v:54`**: `rd_wr_en` is undefined -- must be `rd_wen` (the actual port name). Won't compile as-is
- [x] **Architecture.md module hierarchy**: says `sram.v`/`boot.v` but actual files are `tcm.v`/`bootloader.v`

---

## Phase 1: CPU Core (get a working RV32EC)

### 1.2 ALU (`src/alu.v`)

The nibble-serial adder and comparison logic are implemented. Missing pieces:

- [ ] Add SUB case (`4'b1000`) -- route `sum[3:0]` (adder already inverts B via `b_inv`)
- [ ] Add SLT case (`4'b0010`) -- result = `{3'b0, cmp_out}` on final nibble only, else `4'b0`
- [ ] Add SLTU case (`4'b0011`) -- same structure, unsigned compare
- [ ] Add CZERO.EQZ (`4'b1110`) -- result = `(rs2 == 0) ? 4'b0 : a_in`. Needs full-word rs2 zero check; discuss approach (accumulate across nibbles or let CPU FSM handle)
- [ ] Add CZERO.NEZ (`4'b1111`) -- inverse condition
- [ ] Verify comparison output for all branch types: BEQ (XOR->EQ), BNE (XOR->NE), BLT (SLT signed), BGE (SLT inverted), BLTU (SLTU unsigned), BGEU (SLTU inverted)

Unit tests (`test/unit/alu/test_alu.py`):
- [ ] add_basic, add_carry_propagation, add_overflow_wrap
- [ ] sub_basic, sub_borrow_propagation, sub_negative_result
- [ ] and/or/xor_basic, bitwise_all_zeros, bitwise_all_ones
- [ ] slt_positive, slt_negative, slt_equal, sltu_unsigned
- [ ] czero_eqz, czero_nez
- [ ] carry_chain_across_nibbles, cmp_out_accumulation_across_nibbles

Shifter tests:
- [ ] sll/srl/sra by {0, 1, 16, 31}, nibble_extraction_all_positions

Multiplier tests:
- [ ] positive*positive, negative*positive, negative*negative, zero, max*max, min*min, product_nibble_extraction

### 1.3 Register File (`src/registers.v`)

Rotating shift-register design. Critical constraint: every register rotates every cycle. The CPU FSM MUST be in lockstep with rotation -- if misaligned by 1 cycle, all reads are garbage.

- [ ] Fix `rd_wr_en` -> `rd_wen` bug
- [ ] Verify rotation direction and nibble output position (`register[7:4]` as output -- is this correct for nibble 0 on cycle 0?)
- [ ] Verify write injection: `{register[3:0], register[31:8], rd_nibble}` -- confirm this replaces the correct nibble position during rotation
- [ ] Verify gp/tp nibble generation matches Architecture.md (`gp=0x000400`, `tp=0x400000`)
- [ ] Verify x0 is truly read-only zero (no storage allocated)

Unit tests (`test/unit/registers/test_registers.py`):
- [ ] x0_reads_zero, x0_write_ignored
- [ ] gp_reads_0x000400, tp_reads_0x400000
- [ ] write_then_read_nibble_serial (full 8-cycle write, then 8-cycle read)
- [ ] write_all_storage_registers (x1, x2, x5-x15)
- [ ] simultaneous_rs1_rs2_different_regs, simultaneous_rs1_rs2_same_reg
- [ ] no_cross_contamination_between_regs
- [ ] reset_clears_all_registers
- [ ] rd_wr_en_low_does_not_corrupt

### 1.4 Decoder (`src/decoder.v`)

Has structure for all major instruction groups but many cases produce no useful output. Needs completing:

**RV32I (32-bit) -- incomplete stubs:**
- [ ] OP-IMM (`5'b00100`): derive `alu_opcode` from `funct3` + `funct7[5]` for SRAI vs SRLI. Currently just a comment
- [ ] OP (`5'b01100`): derive `alu_opcode` from `funct3` + `funct7`. Includes SUB (funct7[5]=1), Zicond (funct7=0000111). Currently just a comment
- [ ] BRANCH (`5'b11000`): set `alu_opcode` based on branch type (BEQ/BNE->XOR `4'b0100`, BLT/BGE->SLT `4'b0010`, BLTU/BGEU->SLTU `4'b0011`). Set `mem_opcode[0]` for polarity invert (BNE/BGE/BGEU). Currently no alu_opcode or mem_opcode set
- [ ] JAL (`5'b11011`): compute J-type immediate (done), verify rd assignment
- [ ] JALR (`5'b11001`): verify immediate sign extension (done)

**RV32C (16-bit) -- missing immediates and dispatch:**
- [ ] C.ADDI4SPN (Q0 f3=000): compute `nzuimm` immediate from scattered bits
- [ ] C.LW (Q0 f3=010): compute offset immediate `{instr[5], instr[12:10], instr[6], 2'b00}`
- [ ] C.SW (Q0 f3=110): compute offset immediate (same encoding as C.LW)
- [ ] Zcb (Q0 f3=100): implement C.LBU/C.LHU/C.LH/C.SB/C.SH dispatch
- [ ] C.JAL (Q1 f3=001): compute CJ-type 11-bit signed immediate
- [ ] C.ADDI16SP / C.LUI (Q1 f3=011): split on `rd==2` vs other; compute immediates
- [ ] C.SRLI/SRAI/ANDI and CA-type (Q1 f3=100): dispatch on `instr[11:10]` and `instr[12]`; set alu_opcode for each subcase (SUB=`4'b1000`, XOR=`4'b0100`, OR=`4'b0110`, AND=`4'b0111`, C.NOT=XOR with all-ones)
- [ ] C.J (Q1 f3=101): compute CJ-type 11-bit signed immediate
- [ ] C.BEQZ (Q1 f3=110): compute CB-type 8-bit signed immediate
- [ ] C.BNEZ (Q1 f3=111): compute CB-type 8-bit signed immediate
- [ ] C.SLLI (Q2 f3=000): compute shift amount immediate
- [ ] C.LWSP (Q2 f3=010): compute `{instr[3:2], instr[12], instr[6:4], 2'b00}` immediate
- [ ] C.JR/MV/ADD/JALR/EBREAK (Q2 f3=100): dispatch on `instr[12]` and `rs2==0`; set `is_jalr`, `is_alu_reg`, etc.
- [ ] C.SWSP (Q2 f3=110): compute `{instr[8:7], instr[12:9], 2'b00}` immediate
- [ ] C.SWTP (Q2 f3=111): per ISA.md -- `mem[tp + offset] = rs2`. Not in decoder yet. Decide if implementing now or deferring

Unit tests -- RV32I (`test/unit/decoder/test_decoder_rv32i.py`):
- [ ] load_byte/half/word_signed, load_byte/half_unsigned, load_immediate_sign_extension, load_register_fields
- [ ] store_byte/half/word, store_immediate_reconstruction, store_register_fields
- [ ] addi_basic, addi_min_max, slti_sltiu, xori_ori_andi, slli_srli_srai_opcode, srai_vs_srli_funct7
- [ ] add_sub_funct7_distinguishes, shift_opcodes, logical_opcodes, slt_sltu_opcodes
- [ ] czero_eqz_opcode, czero_nez_opcode
- [ ] branch_all_types, branch_immediate_sign_extension
- [ ] jal/jalr_fields_and_immediates, lui/auipc_upper_immediate

Unit tests -- RV32C (`test/unit/decoder/test_decoder_rv32c.py`):
- [ ] Q0: caddi4spn, clw, csw, zcb_byte_halfword
- [ ] Q1: cnop, caddi, cjal, cli, clui, caddi16sp, csrli, csrai, candi, csub/xor/or/and, cj, cbeqz, cbnez
- [ ] Q2: cslli, clwsp, cjr, cmv, cadd, cjalr, cmul, cswsp
- [ ] prime_register_decode_x8_to_x15, full_register_decode
- [ ] compressed_flag_set/clear

### 1.5 CPU FSM (`src/cpu.v`)

All FSM states are currently empty comments. This is the central piece.

**Design decisions needed before implementing:**
- [ ] **LOAD_WB problem**: after MEM returns 32-bit `mem_rdata`, the loaded value must be sign/zero-extended and written to rd nibble-serially (8 cycles). Options: (a) add a LOAD_WB state that runs 8 nibble cycles, (b) repurpose EXECUTE to write mem_rdata through the ALU, (c) buffer the full word and use MEM state for writeback. Architecture.md doesn't address this -- needs resolving
- [ ] **Shift/multiply dispatch**: CPU FSM needs to know when to route through shifter vs multiplier vs nibble-serial ALU. Decoder produces `alu_opcode` but no `is_mul`/`is_shift` flag. Options: (a) CPU FSM decodes alu_opcode locally, (b) add decoder outputs
- [ ] **Register rotation alignment**: document which cycle-phase each FSM state must enter on to keep register file reads/writes aligned. The shift-register rotates every clock edge regardless of FSM state -- the FSM must account for this drift when not in EXECUTE

**Implement FSM states:**
- [ ] FETCH: assert `mem_read`, route PC to `mem_addr`, wait for `mem_ready`. Latch `mem_rdata` into `instr`. Handle compressed: if `instr[1:0] != 2'b11`, zero-extend upper 16 bits
- [ ] DECODE: 1 cycle. Clear `alu_carry`, set `alu_cmp=1`. Decoder is combinational so outputs are valid immediately. Mux `alu_b_nibble` source: `rf_rs2_nibble` for reg-reg, `dec_imm[nibble_ct*4+:4]` for immediate ops
- [ ] EXECUTE: 8 cycles (RV32I) or 4 (RV32C). Each cycle: read rs1/rs2 nibble from register file, feed ALU, write result nibble to rd. Propagate carry and cmp. Handle special datapaths (shifts, multiply) differently
- [ ] WRITEBACK: compute next PC. Normal: `PC + (is_compressed ? 2 : 4)`. Branch taken: `PC + imm`. JAL: `PC + imm`, write old PC+N to rd. JALR: `(rs1 + imm) & ~1`, write old PC+N to rd
- [ ] MEM: load/store only. Compute EA = rs1 + imm (already in ALU result?). Assert `mem_read` or `mem_write`, set `mem_addr`, `mem_wdata`, `mem_size`. Wait `mem_ready`. For loads: enter LOAD_WB or handle writeback here
- [ ] `mem_size` handling: derive from `dec_mem_opcode[1:0]`. On load: sign-extend (byte->32, half->32) or zero-extend based on `dec_mem_opcode[2]`
- [ ] Branch resolution: after EXECUTE, check `alu_cmp_out` XOR `dec_mem_opcode[0]` (polarity invert for BNE/BGE/BGEU) to decide taken/not-taken

Unit tests (`test/unit/cpu/test_cpu.py`):
- [ ] Reset & fetch: reset_pc_zero, reset_registers_zero, fetch_from_correct_address, fetch_stall_on_mem_not_ready
- [ ] 32-bit execute: add/sub/and/or/xor/slt/sltu end-to-end (8 cycles), sll/srl/sra, lui, auipc
- [ ] Load/store: lw/sw round-trip, lb/lh sign extension, lbu/lhu zero extension
- [ ] Branches: beq/bne taken/not-taken, blt/bltu/bge/bgeu
- [ ] Jumps: jal (link+jump), jalr (rs1-based)
- [ ] Conditional: czero_eqz, czero_nez
- [ ] Compressed: caddi (4-cycle), cli, cmv, cadd, cmul, cjal/cj, cbeqz/cbnez, clw/csw
- [ ] Special: gp/tp read correctly, x0 writes ignored
- [ ] Pipeline: back-to-back ALU, memory stall, nop

**Python encoding helpers** (needed for CPU tests):
- [ ] Write `rv32i_encode.py` (or port from `test/rv32i_encode.py` if compatible) with functions to generate instruction words for each RV32I type
- [ ] Write `rv32c_encode.py` for compressed instruction encoding

### 1.6 Bootloader (`src/bootloader.v`)

FSM logic is present and mostly complete. Verify and fix:

- [ ] Verify FETCH->WRITE_TCM->FETCH loop is correct (rom_read deasserted after rom_ready acknowledged)
- [ ] Verify `rom_addr` computation: `FLASH_BASE + {word_idx, 2'b00}` = byte address. Confirm QSPI expects byte addressing
- [ ] Verify `tcm_addr` is word address (matches TCM Port B which is word-addressed)
- [ ] Verify 512-word count covers full 2 KB TCM

Unit tests (`test/unit/bootloader/test_bootloader.py`):
- [ ] reset_holds_boot_done_low
- [ ] idle_to_fetch_on_reset_deassert
- [ ] flash_addr_starts_at_0x001000, flash_read_asserted
- [ ] tcm_write_one_cycle, tcm_addr_correct
- [ ] word_index_increments, all_512_words_copied, boot_done_after_512
- [ ] flash_stall_fsm_waits

### 1.7 QSPI Controller (`src/qspi.v`)

All states are empty comments. Needs full implementation:

- [ ] IDLE: on `read` or `write`, assert correct CS based on address routing (tinymoa.v does this externally -- verify who owns CS), transition to CMD
- [ ] CMD: shift out SPI command byte (0x03 for read, 0x02 for write) at 4 bits/cycle (QSPI mode, 2 cycles)
- [ ] ADDR_TX: shift out 24-bit address at 4 bits/cycle (6 cycles)
- [ ] DATA_RX: clock in data from `spi_data_in` at 4 bits/cycle (8 cycles for 32-bit word). Assemble into `rdata`
- [ ] DATA_TX: clock out `wdata` to `spi_data_out` at 4 bits/cycle (PSRAM write)
- [ ] DONE: deassert CS, assert `ready` for 1 cycle, return to IDLE
- [ ] `spi_data_oe` control: output enable only during CMD, ADDR_TX, DATA_TX (not during DATA_RX)
- [ ] `bit_cnt` logic: counts through each phase, transitions on phase completion
- [ ] `size` handling: byte/half/word affects DATA_RX/TX length (2/4/8 cycles at 4b/cycle)

Unit tests (`test/unit/qspi/test_qspi.py`):
- [ ] reset_all_cs_deasserted, reset_clk_low
- [ ] flash_read_cs_selection, flash_read_cmd/addr/data phases
- [ ] psram_a/b_read_cs_selection, psram_write_data_tx
- [ ] ready_asserted_after_done, cs_deasserted_after_done
- [ ] spi_data_oe correctness, byte/half/word modes
- [ ] back_to_back_reads, clk_toggles_only_during_transaction

### 1.8 Top-Level Wiring (`src/tinymoa.v`)

- [ ] Verify all submodule port names match after renames (cpu, bootloader, tcm, qspi, dcim)
- [ ] Fix module name mismatch: tinymoa.v instantiates `tinymoa_dcim` but module is now `tinymoa_dcim_core` in `src/dcim/dcim.v` -- either rename the module or add a wrapper
- [ ] Verify address decode ranges match Architecture.md
- [ ] Verify TCM Port B mux: bootloader before `boot_done`, DCIM after
- [ ] Verify `cpu_nrst` gating: CPU held in reset until `boot_done`
- [ ] Verify QSPI mux: bootloader before `boot_done`, CPU after
- [ ] Verify DCIM MMIO: `is_periph && cpu_read`/`cpu_write` routing
- [ ] Verify `tcm_ready` 1-cycle registered delay matches TCM synchronous read latency
- [ ] Check `_unused` signal covers all actually-unused inputs

### 1.9 TCM (`src/tcm.v`)

Behavioral model is complete. Only testing needed:

Unit tests (`test/unit/tcm/test_tcm.py`):
- [ ] port_a/b_write_read_latency_one_cycle
- [ ] concurrent access (different/same address)
- [ ] Write patterns: all zeros, all ones, alternating
- [ ] Address boundaries: 0, 511
- [ ] Back-to-back reads, port isolation

### 1.10 Counter (`src/counter.v`)

Implementation is complete. Only testing needed:

Unit tests (`test/unit/counter/test_counter.py`):
- [ ] en increments, wen loads, reset clears
- [ ] c_out on overflow
- [ ] Parameterized widths (3-bit nibble counter, 24-bit PC)

---

## Phase 2: FPGA Bring-up (Alchitry Cu V2 -- iCE40UP5K)

### 2.1 FPGA Wrapper (`fpga/top.v`)

- [ ] Map TinyTapeout-style ports (ui_in, uo_out, uio_*) to Alchitry Cu V2 pins
- [ ] Clock source: use iCE40 internal oscillator or PLL for 50 MHz
- [ ] Reset: push-button to `nrst`
- [ ] QSPI I/O: map to board SPI flash or external flash module
- [ ] Debug: route CPU PC or state to LEDs, optional UART

### 2.2 Constraints

- [ ] Write `.pcf` constraints file for iCE40UP5K pin mapping
- [ ] Verify I/O standard (3.3V SB_IO)

### 2.3 First Synthesis

- [ ] Synthesize with `yosys` + `nextpnr-ice40`
- [ ] Fix any synthesis errors (undriven nets, width mismatches, unsupported constructs)
- [ ] Check resource usage: LUTs, BRAMs, DFFs fit in UP5K budget (5280 LUTs, 30 EBR)

### 2.4 TCM on FPGA

- [ ] Confirm behavioral `reg [31:0] mem [0:511]` infers to EBR (block RAM) on iCE40
- [ ] Pre-load boot image: `$readmemh` for simulation, `.mem` init for synthesis
- [ ] Alternative: skip bootloader for FPGA, initialize TCM directly from `.mem` file

### 2.5 FPGA Boot Test

- [ ] Load minimal program (NOP loop or LED toggle) into TCM
- [ ] Verify CPU exits reset, PC increments, instructions execute
- [ ] Verify load/store to TCM works

---

## Phase 3: DCIM Accelerator

### 3.1 Compressor (`src/dcim/compressor.v`)

Module is written. Remaining work:

- [x] Add single-approximate mode via `ifdef SINGLE_APPROX_COMPRESSOR` -- one level of AND/OR (level 1), then exact popcount of 8 remaining bits. Output: 4 bits (range 0-8). Midpoint between double-approx (3-bit, high RMSE at >=4-bit precision) and exact (5-bit, full area cost). The paper recommends single-approx for >=4-bit activations
- [ ] Unit test: verify double-approx output range 0-4, exact output range 0-16, single-approx output range 0-8
- [ ] Unit test: exhaustive sweep of all 65536 16-bit inputs for each mode, compare against Python golden model

### 3.2 DCIM FSM (`src/dcim/dcim.v`)

MMIO block and XNOR generate block are complete. FSM states are comment stubs:

- [x] LOAD_WEIGHTS: **pipeline reads** -- assert next read in the same cycle as latching current data (1 cycle/row instead of 2). First row takes 2 cycles (initial read + wait), remaining N-1 rows take 1 cycle each. Total: N+1 cycles instead of 2N. Distribute bits to column `weight_reg` (runtime transpose)
- [x] FETCH_ACT: read activation word at `act_base + bit_plane`. Next cycle: `act_slice = sram_rdata`. bit_plane counts down from P-1 to 0 (MSB first)
- [x] COMPUTE: shift_acc[col] = (shift_acc[col] << 1) + popcount[col]. If bit_plane > 0: decrement, go to FETCH_ACT. Else: go to STORE_RESULT
- [x] STORE_RESULT: write **signed** results to TCM. Convert in hardware: `sram_wdata = 2 * shift_acc[col] - bias_reg`. `bias_reg` precomputed in IDLE = `cfg_array_size * (2^cfg_precision - 1)`. One shared bias register + combinational signed subtract, sign-extended to 32 bits. 1 cycle per column
- [x] Instantiate 2x `tinymoa_compressor` per column in generate block, sum outputs -> popcount[col]
- [x] Wire popcount into accumulator: `shift_acc[col] <= (shift_acc[col] << 1) + popcount[col]`

Hardware signed conversion cost: 32 subtractors, each computing `(shift_acc << 1) - bias` where `bias = N * (2^P - 1)` is constant for the entire inference (computed once from cfg_precision and cfg_array_size). One shared bias register + 32 parallel subtract-from-shifted-acc. Adds ~32 x 12-bit subtractors (~400 gates). Saves the CPU a 32-iteration loop after every inference.

Updated cycle counts (with pipelined LOAD_WEIGHTS):

| Scenario | Formula | 1-bit | 4-bit |
|----------|---------|-------|-------|
| With reload | (N+1) + 3P + N + 3 | 33 + 3 + 32 + 3 = **71** | 33 + 12 + 32 + 3 = **80** |
| Without reload | 3P + N + 3 | 3 + 32 + 3 = **38** | 12 + 32 + 3 = **47** |

### 3.3 DCIM Unit Tests (`test/unit/dcim/test_dcim.py`)

- [ ] MMIO register read/write for all 6 registers
- [ ] cfg_start self-clears, status_busy/done flags
- [ ] Weight loading: correct SRAM addresses, transpose distribution, pipelined timing
- [ ] Compute: 1-bit/2-bit/4-bit precision, shift accumulation
- [ ] XNOR output correctness
- [ ] Store result: correct addresses, **signed values** match `2*acc - bias`
- [ ] End-to-end: identity weights, all-ones weights, skip-reload
- [ ] Compressor mode sweep: double-approx, single-approx, exact -- verify RMSE thresholds

### 3.4 Golden Model

- [ ] Python NumPy reference: MB-XNOR MVM with selectable precision
- [ ] Implement all three compressor modes (double-approx, single-approx, exact) in Python
- [ ] RMSE comparison: < 7% for double-approx, < 3% for single-approx, 0% for exact
- [ ] Signed output verification: compare hardware signed results against golden model

### 3.5 Activation Pre-Transpose (CPU Software)

The CPU pre-transposes activations into bit-planar format in software before writing to TCM. Cost on the nibble-serial CPU:

- For 32 activations at P-bit precision: ~32 x P load-shift-store operations
- On the nibble-serial core (~10 cycles/instruction), roughly 320-1280 cycles for 1-4 bit
- This is small relative to the DCIM compute time (38-80 cycles) only because the CPU does it once per inference batch, not per MVM

No hardware transpose needed -- keep the DCIM datapath simple.

---

## Phase 4: Integration Tests

- [ ] CPU + TCM: boot from pre-loaded TCM, run simple program (counter, memory sweep)
- [ ] CPU + bootloader + QSPI: boot from flash, run from TCM
- [ ] CPU + DCIM: write weights via MMIO, fire START, poll DONE, read signed results
- [ ] Full system: boot -> run -> DCIM inference -> read back

---

## Documentation (update as work proceeds)

- [ ] Fix Architecture.md file hierarchy (sram.v->tcm.v, boot.v->bootloader.v)
- [ ] ISA.md: clean up duplicate content (currently has two copies of several sections)
- [ ] Bootloader.md: pin down flash offset (0x1000) and exact word count
- [x] DCIM.md: update after compressor single-approx mode is added, update cycle counts for pipelined LOAD_WEIGHTS, update signed output description

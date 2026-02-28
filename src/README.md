
# TinyMOA Source

This directory contains the hardware sources for TinyMOA: Verilog modules, LEF snippets, and small helper scripts used to build, simulate, and inspect the processor and the CIM accelerator.

We use a 4b datapath to save on tile space, thus processing each 32b instruction in 8 cycles. `input [2:0] nibble_counter` is used in most modules to keep track of each cycle, sequencing 4 bits at a time to process and produce a 32b result.

The RISC-V compressed (C) 16b instruction set extension uses 4 cycles per 16b instruction, enabling quicker execution. However, `C.MUL16` produces a 32b value from two 16b inputs, thus taking 8 cycles regardless.

`tinymoa.v` is the top-level module, implementing the full RISC-V CPU (with external QSPI flash/PSRAM interfaces) and the CIM accelerator. The `core.v` module implements a raw RISC-V (`RV32EC`) execution core that wraps sequential 4b datpath into a 32b datapath but intentionally leaves out external memory interfaces for generic usage outside of just TinyTapeout.

*This document is WIP*

## Contents

```python
src/
├── alu/            # ALU is split for ease of implementation
│   ├── alu.v
│   ├── multiplier.v
│   └── shifter.v
├── cim/            # Compute-in-Memory accelerator modules
│   ├── core.v      # CIM accelerator core
│   ├── adc.v
│   ├── cell.v
│   ├── compressor.v
│   ├── control.v
│   ├── corelet.v
│   └── README.md
├── memory/         # External TT QSPI flash/PSRAM memory modules
│   ├── ram.v
│   ├── flash.v
│   └── README.md
├── shared/         # Shared components
│   ├── uart.v
│   └── README.md
├── core.v          # Raw generic 32b CPU execution core w/o memory
├── counter.v       # PC
├── registers.v     # RV32E register file
├── decoder.v       # RV32I, RV32C, and custom instruction decoder
├── tinymoa.v       # Top-level wrapper for CPU, memory, CIM integration
└── README.md
```
To build or synthesize for FPGA, follow the instructions in [fpga/README.md](../fpga/README.md) and ensure your local toolchain is set up.

## Where to look next
- Instruction set: [docs/ISA.md](../docs/ISA.md)
- CIM architecture and pseudocode: [docs/CIM.md](../docs/CIM.md)
- FPGA flow: [fpga/README.md](../fpga/README.md)
- Tests and simulation: [test/README.md](../test/README.md)
- FPGA flow: [fpga/README.md](../fpga/README.md)

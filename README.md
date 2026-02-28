#  TinyMOA

A minimal RISC-V CPU with a Compute-in-Memory (CIM) accelerator for performing efficient neural network inference using analog matrix multiplications - all built on top of [TinyQV](https://github.com/MichaelBell/tinyQV) by Michael Bell.

TinyMOA is not meant to be a fully general-purpose core and many design decisions are optimized toward the CIM use case: minimal die area, high code density, and tight coupling to the
crossbar interface.

## Purpose

Modern GPUs spend most of their power budget *moving data*, not computing. While performant at small scale for graphics rendering, it is increasingly inefficient as model sizes grow for AI/ML or LLM use-cases.

Compute-in-Memory (CIM) eliminates this bottleneck by processing data where it is stored, removing the data bus entirely. Similar to your brain, it doesn't separate memory from thought, both are processed in the same place.

CIM often uses resistive RAM (RRAM) which uses memristors to store continuous (analog) values in the form of conductance like a variable resistor. After loading memory initially, you can use Ohm's law to perform a single matrix-vector multiplication (MVM) near instantaneously.

The issue with RRAM is that it requires exotic materials and non-standard fabrication processes that lock it behind expensive, specialized fabs that are out of reach for most researchers.

### Research Question

Using open-source PDKs, tooling, and fabrication processes, can emulated CMOS 3T1C memristor cells obtain 30-40x the efficiency (GOPS/W) over NVIDIA's H100/H200-class hardware?

If so, this approach could significantly democratize CIM research for students and institutions without access to exotic fabrication processes.


<!-- TODO: block diagram — CPU -> CIM array -> crossbar -->

<!-- TODO: GOPS/W comparison bar chart vs H100/H200 -->

## Architecture

### CPU Core

The RISC-V core is directly based on [TinyQV](https://github.com/MichaelBell/tinyQV) by [Michael Bell](https://github.com/MichaelBell). TinyQV is a RV32EC SoC designed for [Tiny Tapeout](https://tinytapeout.com/), built to fit a working RISC-V core in the smallest possible silicon area. The serial 4-bit bus architecture, register file design, and pipeline structure are all his work. *TinyMOA would not exist without any of it*.

The original additions in TinyMOA are test-suite alterations, incrementally restructured instruction decoder, the MOA custom instruction extensions, the CIM hardware interface, and the memristor crossbar array.

### Why RV32EC?

| Choice | Reason |
|--------|--------|
| RV32 | 32-bit RISC-V is the smallest ISA with mature C compiler support (GCC, LLVM) |
| E (Embedded) | Cuts the register file from 32 to 16 registers, saving die/routing space |
| C (Compressed) | 16-bit instructions for common operations. Doubles code density and halves execution time |

## Extensions Over Base RV32EC

| Extension | Description |
|-----------|-------------|
| MOA.V | 8 custom 32-bit instructions to load, configure, and fire the CIM array |
| C.MUL16 | 16x16 -> 32-bit multiply in a single compressed instruction |
| C.LWTP, C.SWTP | Fast load/store through the thread pointer peripheral window |
| C.SCXT, C.LCXT | Single-instruction save/restore of all compressed registers (x8-15) |
| Zcb | Byte-wise common operations |
| Zicsr | CSR read/write for hardware configuration |
| Zicond | Conditional zeroing without branches |

### Why a 4-bit Serial Bus?

Instead of 32-bit parallel internal buses, registers are read and written *4 bits per clock cycle*, completing a full 32-bit operation every 8 cycles. However, compressed 16-bit instructions take 4 cycles to complete except for `C.MUL16` which produces a 32-bit value from 16-bit inputs.

This tradeoff sacrifices latency for a dramatic reduction in routing width and flip-flop count which allows any of this to fit in a small area such as TinyTapeout.

## Documentation

- [ISA Reference](./docs/ISA.md) — instruction encoding, custom extensions, full opcode map
- [CIM Architecture](./docs/CIM.md) — crossbar hardware, control signals, weight loading, inference pseudocode
- [Doc Index & Quick Reference](./docs/README.md) — register table, format cheatsheet, what's in/out

## Status

Work in progress.


# TinyMOA

## Overview

TinyMOA is a custom RISC-V processor based on [TinyQV](https://github.com/MichaelBell/tinyQV/tree/main) designed for Compute-in-Memory (CIM) operations using emulated CMOS memristor crossbar arrays. It extends the minimal `RV32EC` instruction set with a 16x16 multiply instruction and custom CIM instructions for efficient neural network inference.
- The base ISA is `RV32EC`: 32b RISC-V Embedded (16 registers instead of 32) + Compressed (16b instruction extension).
- Custom 16x16 multiply instruction (C.MUL16)
- Custom CIM instructions to manage the memristor crossbar array
- Simple blocking/stallinng architecture

Index
- [Compute-in-Memory](./CIM.md)
- [Instruction Types](#instruction-types)
- [RV32E Registers](#rv32e-registers)
- [Compressed Register Subset](#compressed-register-subset)
- [Instruction Set Summary](#instruction-set-summary)
- [Standard 32b Instructions](#32-bit-instruction-formats)
- [Compressed 16b Instructions](#16b-quadrants-0-2-custom)

## Compute-in-Memory

[See here for an overview](./CIM.md)

## Instruction Types

TinyMOA supports both 32-bit and 16-bit (compressed) instructions. The instruction type determines how the  bits are organized

### 32-bit Instruction Formats

Base RV32I instruction forms (unaffected by 16 vs 32 register count with RV32E)

| Type | Format | Use Case | Examples |
|------|--------|----------|----------|
| **R** | `[funct7][rs2][rs1][funct3][rd][opcode]` | Two source registers, one destination | ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, ... |
| **I** | `[imm[11:0]][rs1][funct3][rd][opcode]` | One source register, one immediate value, loads | ADDI, ANDI, LW, LH, LB, JALR, ... |
| **S** | `[imm[11:5]][rs2][rs1][funct3][imm[4:0]][opcode]` | Store to memory using split immediate field | SW, SH, SB, ... |
| **B** | `[imm[12\|10:5]][rs2][rs1][funct3][imm[4:1\|11]][opcode]` | Conditional branches and offsets | BEQ, BNE, BLT, BGE, BLTU, BGEU, ... |
| **U** | `[imm[31:12]][rd][opcode]` | Load large upper immediate (20 bits) | LUI, AUIPC, ... |
| **J** | `[imm[20\|10:1\|11\|19:12]][rd][opcode]` | Unconditional jumps | J, JAL, ... |

### 16-bit Compressed Formats

Compressed instructions use different formats to fit operations into 16 bits:

| Type | Format | Use Case | Examples |
|------|--------|----------|----------|
| **CR** | `[funct4][rd/rs1][rs2][op]` | Register operations | C.ADD, C.MV, C.JR, ... |
| **CI** | `[funct3][imm][rd/rs1][imm][op]` | Immediate ops | C.ADDI, C.LI, C.LWSP, ... |
| **CSS** | `[funct3][imm][rs2][op]` | Stack-relative store | C.SWSP, ... |
| **CIW** | `[funct3][imm][rd'][op]` | Wide immediate | C.ADDI4SPN, ... |
| **CL** | `[funct3][imm][rs1'][imm][rd'][op]` | Load from memory | C.LW, ... |
| **CS** | `[funct3][imm][rs1'][imm][rs2'][op]` | Store to memory | C.SW, ... |
| **CB** | `[funct3][offset][rs1'][offset][op]` | Conditional branch | C.BEQZ, C.BNEZ, ... |
| **CJ** | `[funct3][jump target][op]` | Unconditional jump | C.J, C.JAL, ... |

> NOTE: `rd'`, `rs1'`, `rs2'` denote compressed registers (x8-x15 only)

## RV32E Registers

Since TinyMOA uses RV32E with 16 registers (`x0-x15`) instead of 32, register usage follows standard but adjusted RISC-V calling conventions. Note that `$gp` and `$sp` are pseudo-hardcoded such that since they are read over 8 cycles, they *generate* the fixed value instead of storing it as a constant. This saves us roughly 32 FFs in place of some combination logic + 3 comparators (2 for `$gp`, 1 for `$tp`).

| Register | ABI Name | Usage | Saved by |
|----------|----------|-------|----------|
| `x0` | zero | Hardwired to 0 (reads always return 0, writes ignored) | - |
| `x1` | ra | Return address (link register) | Caller |
| `x2` | sp | Stack pointer | Callee |
| `x3` | gp | Global pointer (pseudo-hardcoded to `0x1000400`) | - |
| `x4` | tp | Thread pointer (pseudo-hardcoded to `0x800000`) | - |
| `x5-7` | t0-t2 | Temporary registers | Caller |
| `x8` | s0/fp | Saved register / Frame pointer | Callee |
| `x9` | s1 | Saved register | Callee |
| `x10-x11` | a0-a1 | Function arguments / return values | Caller |
| `x12-x15` | a2-a5 | Function arguments | Caller |

> Caller-saved: Function can freely modify these (caller must save if needed)  
> Callee-saved: Function must preserve these (callee must save/restore)

### Compressed Register Subset

Compressed instructions encode registers in 3 bits instead of 4 or 5, limiting them to `x8-x15`. They are written with an apostrophe such as `rd'`, `rs1'`, `rs2'`. Below is the compressed register table:

| 3-bit encoding | Register | ABI Name | Calculation |
|----------------|----------|----------|-------------|
| `000` | `x8` | s0/fp | `8 + 0 = x8` |
| `001` | `x9` | s1 | `8 + 1 = x9` |
| `010` | `x10` | a0 | `8 + 2 = x10` |
| `011` | `x11` | a1 | `8 + 3 = x11` |
| `100` | `x12` | a2 | `8 + 4 = x12` |
| `101` | `x13` | a3 | `8 + 5 = x13` |
| `110` | `x14` | a4 | `8 + 6 = x14` |
| `111` | `x15` | a5 | `8 + 7 = x15` |

These are the most frequently used registers in leaf functions (arguments, saved registers, temporaries). The 3-bit value is added to 8 to get the actual register number.

## Instruction Set Summary
What isn't included (what is replaced)

### 32b
Standard RV32I

### 16b quadrants 0-2 (custom)
Custom CIM instructions

Zicond instructions

C.MUL16

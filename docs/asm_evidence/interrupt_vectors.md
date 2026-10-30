# MetroTRK interrupt-vector templates (GC6E01)

The `crt/interrupt_vectors` owner is the **7,988-byte** interval
`0x800034AC–0x800053E0` in `.init`. It is a table of executable exception-entry
templates, reserved slots and a debugger identification string, not an ordinary
C function. The four other alignment bytes mentioned in earlier completion
reports are outside this interval; do not append four bytes to this object or
include them in its size.

## Source family and provenance

**Origin:** The corresponding library source is Metrowerks MetroTRK for Dolphin,
`TRK_MINNOW_DOLPHIN/Processor/ppc/Generic/exception.s`. The pinned public
[Twilight Princess reconstruction](https://github.com/zeldaret/tp/blob/c8fa8c9e2aab72cf4e5db0e5d1c84a9ea6ee6eb0/libs/TRK_MINNOW_DOLPHIN/debugger/embedded/MetroTRK/Processor/ppc/Generic/exception.s)
provides independently inspectable evidence for the same signature, vector
offsets, entry convention and special cases. That repository publishes its
reconstruction under [CC0 1.0](https://github.com/zeldaret/tp/blob/c8fa8c9e2aab72cf4e5db0e5d1c84a9ea6ee6eb0/LICENSE.md).
This is corroborating decompilation source, not a claim that a proprietary SDK
release was obtained or that its exact version has been established.

**Other decompilations:** The pinned
[Twilight Princess exception assembly](https://github.com/zeldaret/tp/blob/c8fa8c9e2aab72cf4e5db0e5d1c84a9ea6ee6eb0/libs/TRK_MINNOW_DOLPHIN/debugger/embedded/MetroTRK/Processor/ppc/Generic/exception.s)
retains the same hardware register protocol, exception IDs and special entries.

The Colosseum source is an independently authored symbolic assembly
representation of these templates. It uses meaningful instruction mnemonics,
named PowerPC registers, shared entry macros and explicit slot boundaries.
It does not include another project's `macros.inc`, a target-object payload,
generated retail disassembly, or an array of encoded instructions. The
identification string, `Metrowerks Target Resident Kernel for PowerPC`, is
retained as the library's original identifying text.

## Hardware need and local corroboration

**Why it cannot be C:** These entries run at exception entry without a C calling
convention or a usable compiler-generated stack frame. They preserve r2–r4 in SPRG1–SPRG3,
retain the interrupted PC and machine state from SRR0/SRR1, set the instruction
and data translation bits in the state used for transfer, and enter the
debugger through `rfi`. C cannot specify that exact register-entry protocol,
special-register access or exception return instruction.

The existing [TRK initialization](../../src/trk/TRKInit.c) copies selected
`0x100`-byte slots from `gTRKInterruptVectorTable` and flushes their cache
ranges. The existing [TRK interrupt handler](../../src/trk/TRKInterrupt.c)
accepts the preserved PC/state in r2/r4, recovers the original r4 from SPRG3,
and then saves the remaining interrupted context. These callers and consumers
corroborate both the table layout and its register contract.

The vendor's [MetroTRK Reference](https://www.nxp.com/docs/en/reference-manual/METROTRKRM.pdf),
PowerPC appendix, pages 167–170, describes copying exception vectors into their
processor-defined memory locations. The
[MPC750 family manual](https://www.nxp.com/docs/en/reference-manual/MPC750UM.pdf),
exception-processing chapter, documents SRR0/SRR1, SPRGs, translation state and
`rfi`. These hardware references explain the instruction semantics; they do
not establish a particular Colosseum library revision.

## Layout and control transfers

The reserved first slot contains the identification string and zero storage.
The reset entry is at table offset `0x100`. The regular entries use a shared
13-instruction redirect sequence and retain their exception IDs. Special
cases are the machine-check cache invalidations, the shared performance-monitor
and vector-unavailable slot, and three legacy TLB entry wrappers. The table
retains the generic PowerPC library's unused slots and processor-family
entries; their presence is not evidence that Gekko implements every exception
represented by the template library.

The existing public symbols remain at their original addresses:

| Symbol | Address | Role |
| --- | --- | --- |
| `gTRKInterruptVectorTable` | `0x800034AC` | Table start |
| `lbl_80003FF0` | `0x80003FF0` | Existing interior label |
| `lbl_80004000` | `0x80004000` | Existing interior label |
| `gTRKInterruptVectorTableEnd` | `0x800053E0` | End-exclusive table boundary |
| `fn_800053E0` | `0x800053E0` | Existing reset helper; `OSResetSystem(0, 0, 0)` |
| `TRKInterruptHandler` | `0x800C0EAC` | Common debugger entry |

**External branch targets:** The reset entry transfers to `fn_800053E0`, and
all 24 SRR-mediated debugger entries transfer to `TRKInterruptHandler`. The
source declares symbolic relocations to those existing functions. Internal
performance/TLB branches remain inside the template; there are no other
external destinations.

The reset instruction at stored address `0x800035AC` is represented as a
relative branch to `fn_800053E0`, a displacement of `0x1E34`. Copying the slot
without rewriting that instruction preserves its displacement, not its
stored-table destination: execution at physical `0x100` would branch to
`0x1F34`. Preserve and validate the original encoding rather than changing it
to an absolute branch or adding a new runtime relocation. Matching this
stored template does not establish that the copied reset path was exercised.

Regular debugger transfers load the existing handler symbol into SRR0 and
use `rfi`; they are not direct `b`/`bl` calls. The ordinary direct-branch checker
alone therefore cannot validate their destinations. The vector-specific check
must validate each high/low address pair, its SRR0 write, the exception ID,
the translation-state setup and the final `rfi`, as well as the reset branch
and all internal branch destinations.

## Acceptance and accounting

Validate the assembled source object's `.init` extent, all labels, reserved
zeros and slot boundaries against the private original. Resolve symbolic
relocations using the existing linked symbols and compare the complete table;
then require the unchanged canonical DOL and all 25 REL hashes and direct
binary comparisons. Checks should report structural facts and results without
printing or publishing the original payload or disassembly. A failed
comparison remains a failure; it must not be repaired by copying target bytes
into a source object.

The historical hidden synthetic padding marker is not a new function. Making
this owner source-backed adds **zero tracked functions and zero tracked code
or data bytes**: the existing denominators and physical coverage stay intact.
Report the reconstructed executable template as assembly separately from C/C++.
Full source-backed unit completion requires the fresh whole-project report and
its normal source-status/topology checks; it does not follow solely from a
matching final DOL or imply runtime gameplay testing.

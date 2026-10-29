#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047A714-0x8047A760.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047A758[0x8];
u8 lbl_8047A750[0x8];
u8 lbl_8047A748[0x8];
u8 lbl_8047A744[0x4];
u8 lbl_8047A740[0x4];
u8 ResetFunctionQueue_8047A738[0x8];
u8 lbl_8047A730[0x8];
u8 lbl_8047A72C[0x4];
u8 lbl_8047A728[0x4];
u8 __OSLastInterruptTime[0x8];
u8 padding_8047A71A[0x6];
u8 __OSLastInterrupt[0x2];
u8 __OSLastInterruptSrr0[0x4];

#pragma force_active reset

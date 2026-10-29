#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047B398-0x8047B3D0.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047B3C8[0x8];
u8 padding_8047B3C5[0x3];
u8 lbl_8047B3C4;
u8 lbl_8047B3C0[0x4];
u8 lbl_8047B3B8[0x8];
u8 lbl_8047B3B4[0x4];
u8 padding_8047B3B1[0x3];
u8 lbl_8047B3B0;
u8 lbl_8047B3A8[0x8];
u8 lbl_8047B39C[0xC];
u8 padding_8047B39B;
u8 lbl_8047B39A;
u8 lbl_8047B399;
u8 lbl_8047B398;

#pragma force_active reset

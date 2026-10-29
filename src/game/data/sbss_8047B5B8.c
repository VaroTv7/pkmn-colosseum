#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047B5B8-0x8047B670.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047B668[0x8];
u8 lbl_8047B664[0x4];
u8 lbl_8047B660[0x4];
u8 lbl_8047B658[0x8];
u8 lbl_8047B654[0x4];
u8 lbl_8047B650[0x4];
u8 lbl_8047B64C[0x4];
u8 padding_8047B64B;
u8 lbl_8047B64A;
u8 lbl_8047B649;
u8 lbl_8047B648;
u8 lbl_8047B644[0x4];
u8 padding_8047B643;
u8 lbl_8047B642;
u8 lbl_8047B640[0x2];
u8 lbl_8047B63F;
u8 lbl_8047B63E;
u8 lbl_8047B63C[0x2];
u8 lbl_8047B638[0x4];
u8 lbl_8047B634[0x4];
u8 lbl_8047B630[0x4];
u8 lbl_8047B62C[0x4];
u8 lbl_8047B629[0x3];
u8 lbl_8047B628;
u8 lbl_8047B627;
u8 lbl_8047B626;
u8 lbl_8047B625;
u8 lbl_8047B620[0x5];
u8 padding_8047B61E[0x2];
u8 lbl_8047B61C[0x2];
u8 lbl_8047B618[0x4];
u8 padding_8047B615[0x3];
u8 lbl_8047B614;
u8 lbl_8047B610[0x4];
u8 padding_8047B60E[0x2];
u8 lbl_8047B60C[0x2];
u8 lbl_8047B608[0x4];
u8 lbl_8047B600[0x8];
u8 lbl_8047B5F8[0x8];
u8 lbl_8047B5F0[0x8];
u8 lbl_8047B5EC[0x4];
u8 lbl_8047B5E8[0x4];
u8 lbl_8047B5E1[0x7];
u8 lbl_8047B5E0;
u8 lbl_8047B5DA[0x6];
u8 lbl_8047B5D8[0x2];
u8 lbl_8047B5D6[0x2];
u8 lbl_8047B5D5;
u8 lbl_8047B5D4;
u8 lbl_8047B5D0[0x4];
u8 lbl_8047B5C8[0x8];
u8 lbl_8047B5C4[0x4];
u8 padding_8047B5C2[0x2];
u8 lbl_8047B5C1;
u8 lbl_8047B5C0;
u8 lbl_8047B5B8[0x8];

#pragma force_active reset

#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047B3D8-0x8047B460.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047B45C[0x4];
u8 lbl_8047B458[0x4];
u8 lbl_8047B454[0x4];
u8 lbl_8047B450[0x4];
u8 lbl_8047B448[0x8];
u8 lbl_8047B444[0x4];
u8 padding_8047B442[0x2];
u8 lbl_8047B441;
u8 lbl_8047B440;
u8 padding_8047B43D[0x3];
u8 lbl_8047B43C;
u8 lbl_8047B438[0x4];
u8 padding_8047B436[0x2];
u8 lbl_8047B435;
u8 lbl_8047B434;
u8 lbl_8047B430[0x4];
u8 lbl_8047B42C[0x4];
u8 lbl_8047B428[0x4];
u8 lbl_8047B424[0x4];
u8 padding_8047B421[0x3];
u8 lbl_8047B420;
u8 lbl_8047B418[0x8];
u8 lbl_8047B414[0x4];
u8 lbl_8047B410[0x4];
u8 lbl_8047B408[0x8];
u8 lbl_8047B400[0x8];
u8 lbl_8047B3FF;
u8 lbl_8047B3FE;
u8 lbl_8047B3FD;
u8 lbl_8047B3FC;
u8 lbl_8047B3F8[0x4];
u8 padding_8047B3F5[0x3];
u8 lbl_8047B3F4;
u8 lbl_8047B3F0[0x4];
u8 lbl_8047B3EC[0x4];
u8 lbl_8047B3E8[0x4];
u8 lbl_8047B3E0[0x8];
u8 lbl_8047B3D8[0x8];

#pragma force_active reset

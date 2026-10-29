#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047B318-0x8047B358.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047B351[0x7];
u8 lbl_8047B350;
u8 lbl_8047B34C[0x4];
u8 lbl_8047B348[0x4];
u8 lbl_8047B344[0x4];
u8 lbl_8047B340[0x4];
u8 lbl_8047B33C[0x4];
u8 padding_8047B339[0x3];
u8 lbl_8047B338;
u8 lbl_8047B334[0x4];
u8 padding_8047B331[0x3];
u8 lbl_8047B330;
u8 lbl_8047B32C[0x4];
u8 padding_8047B329[0x3];
u8 lbl_8047B328;
u8 lbl_8047B324[0x4];
u8 lbl_8047B320[0x4];
u8 padding_8047B31F;
u8 lbl_8047B31E;
u8 lbl_8047B31D;
u8 lbl_8047B31C;
u8 lbl_8047B31B;
u8 lbl_8047B31A;
u8 lbl_8047B319;
u8 lbl_8047B318;

#pragma force_active reset

#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047B318-0x8047B358.
 * Original symbols establish object extents. Native scalar alignment supplies
 * ordinary gaps; remaining padding uses individual bytes. MWCC emits these
 * definitions in reverse order. Every symbol and gap is independently checked.
 */
#pragma force_active on

u8 lbl_8047B351[0x7] __attribute__((aligned(1)));
u8 lbl_8047B350;
u8 lbl_8047B34C[0x4];
u8 lbl_8047B348[0x4];
u8 lbl_8047B344[0x4];
u8 lbl_8047B340[0x4];
u8 lbl_8047B33C[0x4];
u8 lbl_8047B338;
u8 lbl_8047B334[0x4];
u8 lbl_8047B330;
u8 lbl_8047B32C[0x4];
u8 lbl_8047B328;
u8 lbl_8047B324[0x4];
u8 lbl_8047B320[0x4];
u8 lbl_8047B31E;
u8 lbl_8047B31D;
u8 lbl_8047B31C;
u8 lbl_8047B31B;
u8 lbl_8047B31A;
u8 lbl_8047B319;
u8 lbl_8047B318;

#pragma force_active reset

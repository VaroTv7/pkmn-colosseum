#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047B398-0x8047B3D0.
 * Original symbols establish object extents. Native scalar alignment supplies
 * ordinary gaps; remaining padding uses individual bytes. MWCC emits these
 * definitions in reverse order. Every symbol and gap is independently checked.
 */
#pragma force_active on

u8 lbl_8047B3C8[0x8];
u8 lbl_8047B3C4;
u8 lbl_8047B3C0[0x4];
u8 lbl_8047B3B8[0x8];
u8 lbl_8047B3B4[0x4];
u8 lbl_8047B3B0;
u8 lbl_8047B3A8[0x8];
u8 lbl_8047B39C[0xC];
u8 lbl_8047B39A;
u8 lbl_8047B399;
u8 lbl_8047B398;

#pragma force_active reset

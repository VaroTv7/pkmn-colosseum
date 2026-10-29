#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047AA28-0x8047AA50.
 * Original symbols establish object extents. Native scalar alignment supplies
 * ordinary gaps; remaining padding uses individual bytes. MWCC emits these
 * definitions in reverse order. Every symbol and gap is independently checked.
 */
#pragma force_active on

u8 lbl_8047AA4C[0x4];
u8 lbl_8047AA48[0x4];
u8 lbl_8047AA44[0x4];
u8 lbl_8047AA40[0x4];
u8 lbl_8047AA3C;
u8 lbl_8047AA38[0x4];
u8 lbl_8047AA34[0x4];
u8 lbl_8047AA30[0x4];
u8 lbl_8047AA2C[0x4];
u8 lbl_8047AA28[0x4];

#pragma force_active reset

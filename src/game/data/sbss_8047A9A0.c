#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047A9A0-0x8047A9F0.
 * Original symbols establish object extents. Native scalar alignment supplies
 * ordinary gaps; remaining padding uses individual bytes. MWCC emits these
 * definitions in reverse order. Every symbol and gap is independently checked.
 */
#pragma force_active on

u8 lbl_8047A9E8[0x8];
u8 lbl_8047A9E0[0x8];
u8 padding_8047A9DC;
u8 gTRKInputPendingPtr[0x4];
u8 lbl_8047A9CC[0xC];
u8 lbl_8047A9C8;
u8 lbl_8047A9C4[0x4];
u8 lbl_8047A9C0[0x4];
u8 lbl_8047A9B8[0x8];
u8 lbl_8047A9B4[0x4];
u8 lbl_8047A9B0[0x4];
u8 lbl_8047A9AC;
u8 lbl_8047A9A8[0x4];
u8 lbl_8047A9A4[0x4];
u8 lbl_8047A9A0[0x4];

#pragma force_active reset

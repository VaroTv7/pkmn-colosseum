#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047AA28-0x8047AA50.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047AA4C[0x4];
u8 lbl_8047AA48[0x4];
u8 lbl_8047AA44[0x4];
u8 lbl_8047AA40[0x4];
u8 padding_8047AA3D[0x3];
u8 lbl_8047AA3C;
u8 lbl_8047AA38[0x4];
u8 lbl_8047AA34[0x4];
u8 lbl_8047AA30[0x4];
u8 lbl_8047AA2C[0x4];
u8 lbl_8047AA28[0x4];

#pragma force_active reset

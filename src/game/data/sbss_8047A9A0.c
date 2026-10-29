#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047A9A0-0x8047A9F0.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047A9E8[0x8];
u8 lbl_8047A9E0[0x8];
u8 padding_8047A9DC[0x4];
u8 gTRKInputPendingPtr[0x4];
u8 lbl_8047A9CC[0xC];
u8 padding_8047A9C9[0x3];
u8 lbl_8047A9C8;
u8 lbl_8047A9C4[0x4];
u8 lbl_8047A9C0[0x4];
u8 lbl_8047A9B8[0x8];
u8 lbl_8047A9B4[0x4];
u8 lbl_8047A9B0[0x4];
u8 padding_8047A9AD[0x3];
u8 lbl_8047A9AC;
u8 lbl_8047A9A8[0x4];
u8 lbl_8047A9A4[0x4];
u8 lbl_8047A9A0[0x4];

#pragma force_active reset

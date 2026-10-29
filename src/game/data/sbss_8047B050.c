#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047B050-0x8047B128.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047B124[0x4];
u8 padding_8047B122[0x2];
u8 lbl_8047B120[0x2];
u8 lbl_8047B11A[0x6];
u8 lbl_8047B118[0x2];
u8 lbl_8047B116[0x2];
u8 lbl_8047B114[0x2];
u8 lbl_8047B112[0x2];
u8 lbl_8047B110[0x2];
u8 lbl_8047B108[0x8];
u8 lbl_8047B100[0x8];
u8 lbl_8047B0F8[0x8];
u8 lbl_8047B0F4[0x4];
u8 lbl_8047B0F0[0x4];
u8 lbl_8047B0E8[0x8];
u8 lbl_8047B0E4[0x4];
u8 lbl_8047B0E0[0x4];
u8 lbl_8047B0DC[0x4];
u8 lbl_8047B0D8[0x4];
u8 lbl_8047B0D4[0x4];
u8 lbl_8047B0D0[0x4];
u8 lbl_8047B0CC[0x4];
u8 lbl_8047B0C8[0x4];
u8 lbl_8047B0C4[0x4];
u8 lbl_8047B0C0[0x4];
u8 lbl_8047B0BC[0x4];
u8 lbl_8047B0B8[0x4];
u8 lbl_8047B0B4[0x4];
u8 lbl_8047B0B0[0x4];
u8 lbl_8047B0AC[0x4];
u8 lbl_8047B0A8[0x4];
u8 lbl_8047B0A4[0x4];
u8 padding_8047B0A1[0x3];
u8 lbl_8047B0A0;
u8 lbl_8047B09C[0x4];
u8 lbl_8047B098[0x4];
u8 lbl_8047B094[0x4];
u8 lbl_8047B090[0x4];
u8 lbl_8047B08C[0x4];
u8 lbl_8047B088[0x4];
u8 padding_8047B086[0x2];
u8 lbl_8047B084[0x2];
u8 lbl_8047B080[0x4];
u8 lbl_8047B07C[0x4];
u8 lbl_8047B078[0x4];
u8 lbl_8047B074[0x4];
u8 lbl_8047B070[0x4];
u8 lbl_8047B06C[0x4];
u8 lbl_8047B068[0x4];
u8 lbl_8047B064[0x4];
u8 lbl_8047B060[0x4];
u8 lbl_8047B05F;
u8 lbl_8047B05E;
u8 lbl_8047B05D;
u8 lbl_8047B05C;
u8 lbl_8047B058[0x4];
u8 lbl_8047B054[0x4];
u8 padding_8047B051[0x3];
u8 lbl_8047B050;

#pragma force_active reset

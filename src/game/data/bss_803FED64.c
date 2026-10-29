#include "dolphin/types.h"

/*
 * Zero-initialized storage at .bss 0x803FED64-0x803FFFB0.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_803FFEF0[0xC0];
u8 lbl_803FFDF0[0x100];
u8 lbl_803FFCF0[0x100];
u8 lbl_803FFBF0[0x100];
u8 lbl_803FFBB8[0x38];
u8 __atexit_funcs[0x100];
u8 lbl_803FFA98[0x20];
u8 lbl_803FF598[0x500];
u8 lbl_803FF578[0x20];
u8 lbl_803FF000[0x578];
u8 lbl_803FED78[0x288];
u8 lbl_803FED70[0x8];
u8 padding_803FED69[0x7];
u8 TRK_Use_BBA;
u8 padding_803FED64[0x4];

#pragma force_active reset

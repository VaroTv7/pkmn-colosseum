#include "dolphin/types.h"

/*
 * Zero-initialized storage at .bss 0x803FED60-0x803FFFB0.
 * The preceding TRK state word shares this owner so MWCC can preserve the
 * original eight-byte section alignment; its address-qualified alias is global.
 * Original symbols establish object extents. Native scalar alignment supplies
 * ordinary gaps; remaining padding uses individual bytes. MWCC emits these
 * definitions in reverse order. Every symbol and gap is independently checked.
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
u8 padding_803FED6C;
u8 padding_803FED6B;
u8 padding_803FED6A;
u8 padding_803FED69;
u8 TRK_Use_BBA;
u8 padding_803FED67;
u8 padding_803FED66;
u8 padding_803FED65;
u8 padding_803FED64;

s32 TRK_mainError_803FED60;

#pragma force_active reset

#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_803A1D40[0x20];
u8 lbl_803A1C20[0x120];
u8 lbl_803A1BD8[0x48];
u8 lbl_803A1B90[0x48];
u8 lbl_803A1B80[0x10];
u8 lbl_803A1A48[0x138];
u8 lbl_803A19C8[0x80];
u8 lbl_803A1700[0x2C8];
u8 lbl_803A0700[0x1000];
u8 lbl_8039E700[0x2000];
/* 0x803A1D60-0x803A1F88 is the .bss of the menuSub TU (src/game/menuSub.c). */

#pragma force_active reset

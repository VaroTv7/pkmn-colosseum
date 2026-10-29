#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_803B6E18[0x28];
u8 lbl_803B6E08[0x10];
u8 lbl_803B6DE0[0x28];
u8 lbl_803B6D88[0x58];
u8 lbl_803B6D68[0x20];
u8 lbl_803A9F08[0xCE60];
u8 lbl_803A9EA0[0x68];
u8 lbl_803A9E40[0x60];

#pragma force_active reset

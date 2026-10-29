#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_803FB338[0x48];
u8 lbl_803FB328[0x10];
u8 lbl_803FB318[0x10];
u8 lbl_803FB308[0x10];
u8 lbl_803FB2F8[0x10];
u8 lbl_803FAEF8[0x400];
u8 lbl_803FADF8[0x100];
u8 lbl_803F803B[0x2DBD] __attribute__((aligned(1)));
u8 lbl_803F7A30[0x60B];
u8 lbl_803F6F18[0xB18];
u8 lbl_803F6E40[0xD8];

#pragma force_active reset

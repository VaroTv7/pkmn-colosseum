#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_803A20DC[0x43C];
u8 lbl_803A2094[0x48];
u8 lbl_803A2068[0x2C];
u8 lbl_803A2058[0x10];
u8 lbl_803A204C[0xC];
u8 lbl_803A2040[0xC];

#pragma force_active reset

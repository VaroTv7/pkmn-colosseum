#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_80469030[0x10];
u8 lbl_80469020[0x10];
u8 lbl_80468020[0x1000];
u8 lbl_80467D08[0x318];
u8 lbl_80467CF8[0x10];

#pragma force_active reset

#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_804670B4[0x34];
u8 lbl_80467090[0x24];
u8 lbl_80467050[0x40];
u8 lbl_80467030[0x20];
u8 lbl_80466E50[0x1E0];
u8 lbl_80466E30[0x20];
u8 lbl_80466DE8[0x48];

#pragma force_active reset

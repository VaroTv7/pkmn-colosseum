#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_804673F8[0x888];
u8 lbl_804673D4[0x24];
u8 lbl_804673A0[0x34];
u8 lbl_80467390[0x10];
u8 lbl_80467378[0x18];

#pragma force_active reset

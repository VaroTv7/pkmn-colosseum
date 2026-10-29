#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_804782BC[0x24];
u8 lbl_80478288[0x34];
u8 lbl_80478278[0x10];
u8 lbl_8046DD90[0xA4E8];
u8 lbl_8046D790[0x600];
u8 lbl_8046D760[0x30];
u8 lbl_8046D730[0x30];
u8 lbl_8046D630[0x100];

#pragma force_active reset

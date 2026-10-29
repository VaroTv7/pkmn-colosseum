#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_80465070[0x10];
u8 lbl_80455070[0x10000];

#pragma force_active reset

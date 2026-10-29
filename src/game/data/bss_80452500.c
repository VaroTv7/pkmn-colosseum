#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_804526E0[0x28];
u8 lbl_80452500[0x1E0];

#pragma force_active reset

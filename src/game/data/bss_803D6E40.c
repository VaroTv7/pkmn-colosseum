#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_803D80C6[0x1ED7A] __attribute__((aligned(1)));
u8 lbl_803D6E40[0x1286];

#pragma force_active reset

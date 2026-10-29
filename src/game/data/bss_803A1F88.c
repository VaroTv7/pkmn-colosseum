#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

/* Follows the menuSub TU .bss (0x803A1D60-0x803A1F88). */
u8 lbl_803A1FF8[0x48];
u8 lbl_803A1FC8[0x30];
u8 lbl_803A1F88[0x40];

#pragma force_active reset

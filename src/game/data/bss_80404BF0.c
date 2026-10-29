#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

/* Follows the .bss of win_sprite.c (winSeq/winSprite TU, 0x80404B68-0x80404BF0). */
u8 lbl_804083D0[0x30];
u8 lbl_80408378[0x58];
u8 lbl_80404C68[0x3710];
u8 lbl_80404BF0[0x78];

#pragma force_active reset

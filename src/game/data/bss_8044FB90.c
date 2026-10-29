#include "dolphin/types.h"

/* MWCC emits zero storage in reverse declaration order. Keep every mapped
 * object active so unreferenced retail storage retains its original extent. */
#pragma force_active on

u8 lbl_80451217[0x12E9] __attribute__((aligned(1)));
u8 lbl_80450500[0xD17];
u8 lbl_804504A0[0x60];
u8 lbl_80450098[0x408];
u8 lbl_8044FE14[0x284];
u8 lbl_8044FB90[0x284];

#pragma force_active reset

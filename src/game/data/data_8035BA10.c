#include "dolphin/types.h"

/* Developer diagnostic names already present in the reconstructed source.
 * Recorded symbol extents preserve their NULs; the final bytes are padding. */
#pragma section ".data"
#pragma force_active on

u8 lbl_8035BA10[0x19] = "floorDataBiosGetMainFunc";
u8 lbl_8035BA2C[0x19] = "floorDataBiosGetPostFunc";
u8 padding_8035BA45[0x3] __attribute__((aligned(1))) = {0};

#pragma force_active reset

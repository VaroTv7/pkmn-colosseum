#include "dolphin/types.h"

/* Developer diagnostic names already present in the reconstructed source.
 * Recorded symbol extents preserve their NULs; the final bytes are padding. */
#pragma section ".data"
#pragma force_active on

u8 lbl_8035B060[0xE] = "menuCloseSync";
u8 lbl_8035B070[0x12] = "windowCheckCursor";
u8 padding_8035B082[0x6] __attribute__((aligned(1))) = {0};

#pragma force_active reset

#include "dolphin/types.h"

/* Developer diagnostic names already present in the reconstructed source.
 * Recorded symbol extents preserve their NULs; the final bytes are padding. */
#pragma section ".data"
#pragma force_active on

u8 lbl_80315678[0x11] = "_msgCallCtrlFunc";
u8 padding_80315689[0x7] __attribute__((aligned(1))) = {0};

#pragma force_active reset

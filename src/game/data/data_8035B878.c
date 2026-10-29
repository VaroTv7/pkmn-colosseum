#include "dolphin/types.h"

/* Developer diagnostic names already present in the reconstructed source.
 * Recorded symbol extents preserve their NULs; the final bytes are padding. */
#pragma section ".data"
#pragma force_active on

u8 lbl_8035B878[0xD] = "floorInitMap";
u8 lbl_8035B888[0x15] = "_floorInitCharacters";
u8 padding_8035B89D[0x3] __attribute__((aligned(1))) = {0};

#pragma force_active reset

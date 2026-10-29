#include "dolphin/types.h"

/* Developer diagnostic names already present in the reconstructed source.
 * Recorded symbol extents preserve their NULs; the final bytes are padding. */
#pragma section ".data"
#pragma force_active on

u8 lbl_8035B988[0x19] = "floorDataBiosGetPreSctID";
u8 lbl_8035B9A4[0x1A] = "floorDataBiosGetMainSctID";
u8 lbl_8035B9C0[0x1A] = "floorDataBiosGetPostSctID";
u8 lbl_8035B9DC[0x1A] = "floorDataBiosGetPlaceName";
u8 padding_8035B9F6[0x2] __attribute__((aligned(1))) = {0};

#pragma force_active reset

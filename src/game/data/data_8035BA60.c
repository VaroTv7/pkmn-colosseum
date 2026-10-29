#include "dolphin/types.h"

/* Developer diagnostic names already present in the reconstructed source.
 * Recorded symbol extents preserve their NULs; the final bytes are padding. */
#pragma section ".data"
#pragma force_active on

u8 lbl_8035BA60[0x19] = "floorDataBiosGetCharInfo";
u8 lbl_8035BA7C[0x1B] = "floorDataBiosGetPosListPtr";
u8 lbl_8035BA98[0x23] = "floorDataBiosGetFieldCameraListPtr";
u8 lbl_8035BABC[0x19] = "floorDataBiosSetMapResID";
u8 lbl_8035BAD8[0x1A] = "floorDataBiosSetMainSctID";
u8 lbl_8035BAF4[0x19] = "floorDataBiosGetSunResID";
u8 lbl_8035BB10[0x1E] = "floorDataBiosGetShadowLightID";
u8 lbl_8035BB30[0x1F] = "floorDataBiosGetShadowReciveID";
u8 padding_8035BB4F[0x1] __attribute__((aligned(1))) = {0};

#pragma force_active reset

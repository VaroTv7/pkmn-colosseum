#include "dolphin/types.h"

#pragma section ".data"
#pragma force_active on

extern u8 lbl_8035B8A0[];

/* Auto-carved .data unit 0x8035B8A0..0x8035B904 (4 objects). Non-relocated data as byte-exact u8[]; pointer/jump tables as void*[] for R_PPC_ADDR32 relocations. */

u8 lbl_8035B8A0[20] = {
    0x66, 0x6C, 0x6F, 0x6F, 0x72, 0x44, 0x61, 0x74, 0x61, 0x42, 0x69, 0x6F,
    0x73, 0x47, 0x65, 0x74, 0x50, 0x74, 0x72, 0x00,
};

/* Adjacent developer diagnostic names share this owner because 0x8035B8B4
 * is only four-byte aligned. Their declared extents include the original NULs. */
u8 lbl_8035B8B4[0x15] = "floorDataBiosGetArea";
u8 lbl_8035B8CC[0x19] = "floorDataBiosGetMapResID";
u8 lbl_8035B8E8[0x1A] = "floorDataBiosGetFloorKind";
u8 padding_8035B902[0x2] __attribute__((aligned(1))) = {0};

#pragma force_active reset

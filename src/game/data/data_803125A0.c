#include "dolphin/types.h"

/* ARQInit registers this version through lbl_80478A38. The standard SDK build
 * literal agrees with the tracked string catalog and the CI5 symbol hash. */
#pragma section ".data"
#pragma force_active on

char lbl_803125A0[0x45] =
    "<< Dolphin SDK - ARQ\trelease build: Sep  5 2002 05:34:29 (0x2301) >>";
u8 padding_803125E5[3] __attribute__((aligned(1))) = {0};

#pragma force_active reset

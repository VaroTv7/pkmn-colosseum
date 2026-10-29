#include "dolphin/types.h"

/* PAD's existing version pointer and SDK build convention identify this
 * literal. Its timestamp is also recorded in config/GC6E01/symbolmap/strings.json;
 * CI5 verifies the complete literal and its three zero padding bytes. */
#pragma section ".data"
#pragma force_active on

char lbl_803124B8[0x45] =
    "<< Dolphin SDK - PAD\trelease build: Sep  5 2002 05:34:02 (0x2301) >>";
u8 padding_803124FD[3] __attribute__((aligned(1))) = {0};

#pragma force_active reset

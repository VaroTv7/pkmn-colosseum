#include "dolphin/types.h"

/* Initialized zero storage with the existing mapped identities and extents.
 * CI6 verifies all three original objects and their trailing gap as zero;
 * no runtime purpose is inferred. The source-link alignment guard checks
 * native bytes, symbol offsets/sizes and compiler alignment requirements.
 * See docs/recon/initialized_zero_8038FF64.md. */
#pragma section ".data"
#pragma force_active on

u8 lbl_8038FF64[18] = {0};
u8 lbl_8038FF76[131] __attribute__((aligned(1))) = {0};
u8 lbl_8038FFF9[1] __attribute__((aligned(1))) = {0};
u8 padding_8038FFFA[2] __attribute__((aligned(1))) = {0};

#pragma force_active reset

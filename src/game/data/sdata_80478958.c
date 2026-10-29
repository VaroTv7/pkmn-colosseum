#include "dolphin/types.h"

/* Small game state following the original controller-table alias block.
 * See docs/recon/data_object_bounds.md. */
#pragma force_active on

u8 lbl_80478958[8] = {1};
u32 lbl_80478960[2] = {9, 0};

/* First word: sizeof(lbl_802EF0A8) / 0x1C. The second stored bound is retained
 * without assigning it a new runtime meaning. */
u32 lbl_80478968[2] = {4818, 4785};

#pragma force_active reset

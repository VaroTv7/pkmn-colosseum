#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss2 0x8047E718-0x8047E728.
 * Original symbols establish object extents. Native scalar alignment supplies
 * ordinary gaps; remaining padding uses individual bytes. MWCC emits these
 * definitions in reverse order. Every symbol and gap is independently checked.
 */
#pragma force_active on

const u8 lbl_8047E720[0x8];
const u8 lbl_8047E718[0x8];

#pragma force_active reset

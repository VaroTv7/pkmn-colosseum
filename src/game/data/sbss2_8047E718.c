#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss2 0x8047E718-0x8047E728.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

const u8 lbl_8047E720[0x8];
const u8 lbl_8047E718[0x8];

#pragma force_active reset

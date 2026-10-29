#include "dolphin/types.h"

/* Continuation of the independently reconstructed small game state.
 * The preceding coordinate-pair alias block and following controller-table
 * alias block retain original fallback. See docs/recon/data_object_bounds.md. */
#pragma force_active on

f32 lbl_804788D8[2] = {0.5235988f, 0.0f}; /* caption pulse phase: pi / 6 */
s32 lbl_804788E0[2] = {1, 0};
s32 lbl_804788E8[2] = {1, 0};
u32 lbl_804788F0[2] = {4, 0};
s32 lbl_804788F8[2] = {1, 0};

/* The first sprite count is sizeof(lbl_802E7CE8) / 0x18. */
u32 lbl_80478900[2] = {528, 0};
u32 lbl_80478908[2] = {986, 884};
u16 lbl_80478910[4] = {0, 747, 748, 749};
s16 lbl_80478918 = 3;
s16 lbl_8047891A = 4;
f32 lbl_8047891C = 1.0f;
s16 lbl_80478920 = 60;
s16 lbl_80478922[3] __attribute__((aligned(2))) = {158, 0, 0};
u32 lbl_80478928[2] = {61, 0};
u8 lbl_80478930[8] = {13};
u32 lbl_80478938[2] = {296, 0};
s32 lbl_80478940[2] = {-1, 0};

/* Card-e's MSB-first bit-reader masks. */
u8 lbl_80478948[8] = {0x80, 0x40, 0x20, 0x10, 8, 4, 2, 1};

#pragma force_active reset

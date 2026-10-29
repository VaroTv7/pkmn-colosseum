#include "dolphin/types.h"

/* Small game state and lookup tables used by the existing task, menu and GBA
 * implementations. Keep every mapped object extent: several scalar views
 * occupy the first element of an eight-byte storage object with a zero suffix.
 * The complete 0x150-byte initialized section agrees with the CI6 target hash.
 * No original object supplies bytes to this source. */
#pragma force_active on

/* Task/input defaults (gs_task.c and main.c). */
u8 lbl_80478820[8] = {1};
u8 lbl_80478828 = 5;
u16 lbl_8047882A = 1;
u16 lbl_8047882C = 1;
u8 lbl_8047882E = 1;
u16 lbl_80478830[4] = {1, 0, 0, 0};
u32 lbl_80478838[2] = {0, 0};
u8 lbl_80478840[8] = {1};

/* Menu data count, four move-choice IDs, and signed selection sentinels. */
u32 lbl_80478848[2] = {272, 0};
u16 lbl_80478850[4] = {0xC4, 0xC5, 0xC6, 0xC7};
s32 lbl_80478858 = -1;
s32 lbl_8047885C = -1;
u8 lbl_80478860[8] = {1};
u32 lbl_80478868[2] = {1, 0};
u16 lbl_80478870[4] = {0xE93, 0xE94, 0xE95, 0xE96};

/* Title/options state and its message table. */
s32 lbl_80478878[2] = {3, 0};
u32 lbl_80478880[2] = {6450, 0};
u8 lbl_80478888[8] = {0};
u8 lbl_80478890[8] = {0};
f32 lbl_80478898[2] = {90.0f, 0.0f};
s32 lbl_804788A0[2] = {1, 0};
u32 lbl_804788A8[2] = {1, 0};
u8 lbl_804788B0[8] = {1};
s32 lbl_804788B8[2] = {-1, 0};

/* PDA mode and coordinate pairs. The existing labels partition the pairs;
 * aligned(2) keeps their zero storage and short fields at those boundaries. */
s32 lbl_804788C0 = 90;
u8 lbl_804788C4 = 5;
s16 lbl_804788C8[1] = {0};
u16 padding_804788CA[1] __attribute__((aligned(2))) = {0};
s16 lbl_804788CC = -130;
s16 lbl_804788CE = 40;
s16 lbl_804788D0[1] = {0};
s16 lbl_804788D2 = 64;
u8 lbl_804788D4[4] = {10, 11, 18, 5}; /* filter choice counts */
f32 lbl_804788D8[2] = {0.5235988f, 0.0f}; /* caption pulse phase: pi / 6 */
s32 lbl_804788E0[2] = {1, 0};
s32 lbl_804788E8[2] = {1, 0};
u32 lbl_804788F0[2] = {4, 0};
s32 lbl_804788F8[2] = {1, 0};

/* Menu sequence/sprite counts and battle indicator sprites. The first sprite
 * count is sizeof(lbl_802E7CE8) / 0x18; retain its adjacent stored bound. */
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

/* Card-e's MSB-first bit reader and GBA controller masks/order. The original
 * mapped labels divide each four-byte controller table after its first byte. */
u8 lbl_80478948[8] = {0x80, 0x40, 0x20, 0x10, 8, 4, 2, 1};
u8 lbl_80478950 = 1;
u8 lbl_80478951[3] __attribute__((aligned(1))) = {2, 4, 8};
s8 lbl_80478954 = 1;
s8 lbl_80478955[3] __attribute__((aligned(1))) = {2, 3, 0};
u8 lbl_80478958[8] = {1};
u32 lbl_80478960[2] = {9, 0};

/* First word: sizeof(lbl_802EF0A8) / 0x1C. The second stored bound is retained
 * without assigning it a new runtime meaning. */
u32 lbl_80478968[2] = {4818, 4785};

#pragma force_active reset

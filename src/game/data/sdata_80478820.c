#include "dolphin/types.h"

/* Small game state used by the existing task and menu implementations.
 * The complete coordinate arrays retain their original interior labels in
 * the guarded source-link metadata view. Native C bounds remain unchanged.
 * See docs/recon/small_data_array_aliases.md. */
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

/* The active PDA renderer reads/writes both coordinates of this array. */
s32 lbl_804788C0 = 90;
u8 lbl_804788C4 = 5;
s16 lbl_804788C8[2] = {0, 0};

/* The PDA renderer reads both coordinates. lbl_804788CE and lbl_804788D2
 * are linker labels for element one, not independently allocated objects. */
s16 lbl_804788CC[2] = {-130, 40};
s16 lbl_804788D0[2] = {0, 64};
u8 lbl_804788D4[4] = {10, 11, 18, 5}; /* filter choice counts */

#pragma force_active reset

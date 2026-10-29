/* Included after the existing OS.c source owner to retain its aligned small-
 * data section. No text definitions or references in that owner are changed. */
#include "dolphin/types.h"

#pragma force_active on

/* OSRegisterVersion forwards the supplied version through this format. */
char lbl_8047897C[4] = "%s\n";

/* __OSCurrHeap is a signed heap handle in the allocator's existing source.
 * Its original -1 sentinel is followed by a separate zero padding word. */
volatile s32 lbl_80478980 = -1;
u32 padding_80478984[1] = {0};

/* OSArena.c reads/writes this pointer; OSInit installs the arena's real start. */
void* __OSArenaLo = (void*)-1;
u32 padding_8047898C[1] = {0};

#pragma force_active reset

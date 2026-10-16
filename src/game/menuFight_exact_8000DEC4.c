/**
 * @file menuFight_exact_8000DEC4.c
 * @brief menuFightDrawTargetSecret, 0x8000DEC4 - 0x8000DFF0.
 *
 * Function-boundary carve of the menuFight TU (see menuFight.c). GC/1.3
 * -O4,p with the TU's unit-wide -opt nopeephole, no pragmas.
 */
#include "dolphin/types.h"

typedef struct MenuFightTargetSprite {
    u8 pad_00[6];
    s16 tag;
} MenuFightTargetSprite;

/* menuFightDrawTargetSecret - 0x8000DEC4 | size: 0x12c
 * Shows the target sprite when any of the four secret-move target entries
 * (8-byte stride, id at +4) maps to the sprite's tag; hides it otherwise.
 * MWCC unrolls the four-entry loop by two. */
void menuFightDrawTargetSecret(u8* arg1, u8* arg2) {
    extern void* windowGetParam(u8* a, u32 b);
    extern void winSpriteSetDisp(u8* a, u32 b);
    s32 value;
    u8* entry;
    s32 i;
    entry = (u8*)windowGetParam(arg1, 0);
    for (i = 0; i < 4; i++) {
        switch (*(s32*)(entry + 4 + i * 8)) {
            case 0x45: value = 0x125C; break;
            case 0x46: value = 0x125E; break;
            case 0x47: value = 0x12BE; break;
            case 0x48: value = 0x125D; break;
            default: value = 0; break;
        }
        if (value == ((MenuFightTargetSprite*)arg2)->tag) {
            winSpriteSetDisp(arg2, 1);
            return;
        }
    }
    winSpriteSetDisp(arg2, 0);
}

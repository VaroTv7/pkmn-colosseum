#include "dolphin/types.h"

extern void floorRequestChange(u32);

s32 fn_801CBA90(void)
{
    floorRequestChange(0x395);
    return 0;
}

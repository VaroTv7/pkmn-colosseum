#include "dolphin/types.h"

extern u32 std093_getCurrentGroupID(void);
extern void fn_8018DB68(u32 group, u32 resource);

void std113_mapObjectUnk_8018db68(u32 resource)
{
    fn_8018DB68(std093_getCurrentGroupID(), resource);
}

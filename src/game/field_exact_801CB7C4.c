#include "dolphin/types.h"

extern u32 std093_getCurrentGroupID(void);
extern void* peopleIsInGroup(u32 group, u32 resource);
extern void fn_8018B220(u32 group, u32 resource);
extern void* GSresGetResource(u32 group, u32 resource);
extern void GSmodelStopAnimation(void* model);

void std116_mapObjectStopAnimation(u32 resource)
{
    u32 group = std093_getCurrentGroupID();
    void* model;

    if (peopleIsInGroup(group, resource) != NULL) {
        fn_8018B220(group, resource);
    } else {
        model = GSresGetResource(group, resource);
        if (model != NULL) {
            GSmodelStopAnimation(model);
        }
    }
}

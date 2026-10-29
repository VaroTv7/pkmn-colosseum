#include "dolphin/types.h"

/* Battle-script scratch flags. Existing consumers access all eight bytes.
 * D7B and D7D are original interior linker labels at offsets three and five;
 * the guarded metadata view supplies aliases without shrinking this array.
 * An explicit array initializer retains initialized small-data storage. */
#pragma force_active on

u8 lbl_80478D78[8] = {0};

#pragma force_active reset

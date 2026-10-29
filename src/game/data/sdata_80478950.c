#include "dolphin/types.h"

/* Four controller masks and the Card-e traversal order. Consumers index each
 * complete four-byte array. The original labels at 951 and 955 denote its
 * final three bytes; the guarded link view supplies those interior names
 * without dividing either C array or changing its storage. */
#pragma force_active on

u8 lbl_80478950[4] = {1, 2, 4, 8};
s8 lbl_80478954[4] = {1, 2, 3, 0};

#pragma force_active reset

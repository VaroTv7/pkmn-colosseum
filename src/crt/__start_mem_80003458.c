/* .init 0x80003458 - 0x800034AC: the two memory helpers preceding the
   original interrupt-vector table (fn_80003458 and fn_80003488). */
#define START_MEM_PART
#define START_MEM_PREFIX
#include "src/crt/__start.c"

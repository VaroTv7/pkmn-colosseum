/* .init 0x800053E0 - 0x80005544: the memory helpers following the original
   interrupt-vector table (fn_800053E0, memset, __fill_mem and memcpy). */
#define START_MEM_PART
#define START_MEM_SUFFIX
#include "src/crt/__start.c"

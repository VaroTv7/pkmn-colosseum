#include "dolphin/types.h"

/* OSReset's DMA header buffer, 0x803FB820..0x803FB840. Keep the existing
 * reconstructed layout and 32-byte alignment while the matching reboot
 * code accesses the buffer through an external symbol.
 */
typedef struct ApploaderHeader {
    char date[16];
    u32 entry;
    u32 size;
    u32 rebootSize;
    u32 reserved2;
} ApploaderHeader;

ApploaderHeader Header __attribute__((aligned(32)));

#include "dolphin/types.h"

/* MetroTRK initializes these flags to clear. Register writes set the first
 * two flags and TRKRestoreExtended1Block consumes and clears them. The
 * nine-byte object at 0x80313818 is followed by three bytes of link padding.
 * Explicit .data placement preserves initialized state rather than BSS. */
__declspec(section ".data") u8 gTRKRestoreFlags[9] = { 0 };

/* Keep the following existing MetroTRK data at its four-byte offset inside
 * this eight-byte-aligned owner. Its definitions and symbols are unchanged. */
#include "src/game/data/data_80313824.c"

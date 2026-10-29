#include "dolphin/types.h"

/* DVD diagnostics reconstructed from their existing callsites and the adjacent
 * DVDReadAsync diagnostic. The SDK build stamp is recorded in strings.json.
 * CI5 verifies each literal and the complete 0xA4-byte section by SHA-256. */
#pragma section ".data"
#pragma force_active on

char lbl_80311A24[0x2F] = "DVDRead(): specified area is out of the file  ";
char lbl_80311A54[0x27] = "DVDSeek(): offset is out of the file  ";
u8 padding_80311A7B[5] __attribute__((aligned(1))) = {0};
char lbl_80311A80[0x45] =
    "<< Dolphin SDK - DVD\trelease build: Oct 29 2002 09:56:49 (0x2301) >>";
u8 padding_80311AC5[3] __attribute__((aligned(1))) = {0};

#pragma force_active reset

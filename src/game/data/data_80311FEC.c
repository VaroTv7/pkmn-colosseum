#include "dolphin/types.h"

/* SDK fatal-error text already recorded in
 * config/GC6E01/symbolmap/strings.json. The full source span, including
 * its three zero-padding bytes, matches the private-input section hash. */
#pragma force_active on
char lbl_80311FEC[137] = "\n\n\nEr is een fout opgetreden.\nZet de NINTENDO GAMECUBE uit en\nraadpleeg de handleiding van de\nNintendo GameCube voor nadere\ninstructies.";
u8 padding_80312075[3] __attribute__((aligned(1))) = { 0 };
#pragma force_active reset

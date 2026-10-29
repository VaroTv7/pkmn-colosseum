#include "dolphin/types.h"

/* SDK fatal-error text already recorded in
 * config/GC6E01/symbolmap/strings.json. The full source span, including
 * its three zero-padding bytes, matches the private-input section hash. */
#pragma force_active on
char lbl_80311DB8[153] = "\n\n\nEin Fehler ist aufgetreten.\nBitte schalten Sie den NINTENDO GAMECUBE\naus und lesen Sie die Bedienungsanleitung,\num weitere Informationen zu erhalten.";
u8 padding_80311E51[3] __attribute__((aligned(1))) = { 0 };
#pragma force_active reset

#include "dolphin/types.h"

#pragma force_active on

/* WS_STATUS_SET16 operands for fightFloorSetStatus field 0x3B. These
 * constants also occur in the corresponding direct C status setters.
 * Keep the preceding eight-byte flag block original-backed until its
 * overlapping map labels can describe one genuine source array.
 * See docs/recon/sdata_80478D08_reconstruction.md for typed evidence. */
__declspec(section ".sdata") u16 lbl_80478D80[3] = {0x45, 0x43, 0x40};

/* WS_STATUS_SET16 to fight-floor field 0x3C clears these move-status IDs.
 * fightWazaIsJoutaiSousai checks the same pair, 0x41 and 0x42. */
__declspec(section ".sdata") u16 lbl_80478D86 __attribute__((aligned(2))) = 0x41;
__declspec(section ".sdata") u16 lbl_80478D88 __attribute__((aligned(2))) = 0x42;
__declspec(section ".sdata") u8 padding_80478D8A[2] __attribute__((aligned(1))) = {0};

#pragma force_active reset

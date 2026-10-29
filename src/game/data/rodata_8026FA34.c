#include "dolphin/types.h"

/* Padding is byte-aligned: MWCC otherwise aligns these arrays to four bytes
 * and moves the following strings. Retain every original byte in this owner. */
#pragma force_active on

/* Auto-carved .rodata 0x8026FA34..0x8026FA40 (split from rodata_8026F818.c; 0x8026FA40 belongs to TRKRequestSend's unit). */

const u8 lbl_8026FA34[6] = {
    0x25, 0x30, 0x32, 0x78, 0x20, 0x00,
};

const u8 gap_04_8026FA3A_rodata[2] __attribute__((aligned(1))) = {
    0x00, 0x00,
};

const u8 lbl_8026FA3C[2] = {
    0x0A, 0x00,
};

const u8 gap_04_8026FA3E_rodata[2] __attribute__((aligned(1))) = {
    0x00, 0x00,
};

#pragma force_active reset

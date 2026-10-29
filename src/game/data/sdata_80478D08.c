#include "dolphin/types.h"

#define SDATA __declspec(section ".sdata")
#define BYTE_ALIGNED __attribute__((aligned(1)))

#pragma force_active on

/* Independently reconstructed small-data globals, 0x80478D08..0x80478D86.
 * The original map includes alignment bytes in several scalar extents.
 * Keep the live types used by the callers and name the verified zero padding.
 * See docs/recon/sdata_80478D08_reconstruction.md for evidence and hashes. */

extern char lbl_803751F0[];

/* THPInit passes this version string to OSRegisterVersion. */
SDATA char* lbl_80478D08 = lbl_803751F0;
SDATA u8 padding_80478D0C[4] BYTE_ALIGNED = {0};

/* fightPreloadResources walks 21 (archive, result) pairs, two u16s each. */
SDATA u16 lbl_80478D10 = 21 * 2;
SDATA u8 padding_80478D12[6] BYTE_ALIGNED = {0};

/* Five nonzero intro-effect IDs precede padding in lbl_80375970. */
SDATA u8 lbl_80478D18 = 5;
SDATA u8 padding_80478D19[7] BYTE_ALIGNED = {0};

/* Eleven 12-byte wipe records and eight 24-byte condition-pair records. */
SDATA u32 lbl_80478D20 = 11;
SDATA u8 padding_80478D24[4] BYTE_ALIGNED = {0};
SDATA u32 lbl_80478D28 = 8;
SDATA u8 padding_80478D2C[4] BYTE_ALIGNED = {0};

typedef struct ColosseumEventRow6 {
    u8 mode;
    u8 field_01;
    u16 eventIndex;
    u16 nextIndex;
} ColosseumEventRow6;

/* The three joukenDataGet accessors read one all-zero six-byte event row. */
SDATA ColosseumEventRow6 lbl_80478D30[1] = {{0, 0, 0, 0}};
SDATA u8 padding_80478D36[2] BYTE_ALIGNED = {0};
SDATA u32 lbl_80478D38 = 1;
SDATA u8 padding_80478D3C[4] BYTE_ALIGNED = {0};

/* Counts for lbl_80375AC8, lbl_80375BB8 and lbl_80375CB8 respectively. */
SDATA u32 lbl_80478D40 = 30;
SDATA u8 padding_80478D44[4] BYTE_ALIGNED = {0};
SDATA u32 lbl_80478D48 = 20;
SDATA u8 padding_80478D4C[4] BYTE_ALIGNED = {0};
SDATA u32 lbl_80478D50 = 2;
SDATA u8 padding_80478D54[4] BYTE_ALIGNED = {0};

/* fightWazaCriticalDataBiosGetBunbo supplies the denominator at each stage. */
SDATA u8 lbl_80478D58[5] = {16, 8, 4, 3, 2};
SDATA u8 padding_80478D5D[3] BYTE_ALIGNED = {0};
SDATA u32 lbl_80478D60 = 5;
SDATA u8 padding_80478D64[4] BYTE_ALIGNED = {0};

/* Thirteen live numerator/denominator pairs cover stages -6 through +6. */
SDATA u32 lbl_80478D68 = 13;
SDATA u8 padding_80478D6C[4] BYTE_ALIGNED = {0};
SDATA u32 lbl_80478D70 = 13;
SDATA u8 padding_80478D74[4] BYTE_ALIGNED = {0};

/* Eight zero-initialized battle-script flag bytes. Preserve the existing
 * addressable sublabels at offsets 0, 3 and 5 and the intervening map gaps. */
SDATA u8 lbl_80478D78 = 0;
SDATA u8 padding_80478D79[2] BYTE_ALIGNED = {0};
SDATA u8 lbl_80478D7B = 0;
SDATA u8 padding_80478D7C = 0;
SDATA u8 lbl_80478D7D = 0;
SDATA u8 padding_80478D7E[2] BYTE_ALIGNED = {0};

/* WS_STATUS_SET16 operands for fightFloorSetStatus field 0x3B. These
 * constants also occur in the corresponding direct C status setters. */
SDATA u16 lbl_80478D80[3] = {0x45, 0x43, 0x40};

#pragma force_active reset

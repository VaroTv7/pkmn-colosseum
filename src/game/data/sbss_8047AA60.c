#include "dolphin/types.h"

/*
 * Zero-initialized storage at .sbss 0x8047AA60-0x8047AAF8.
 * The existing symbol map establishes every object boundary. Unrecovered
 * types remain byte storage; padding keeps the original relative addresses.
 * MWCC emits uninitialized definitions in reverse source order. Force-active
 * preserves storage that retail retains without a direct DOL reference.
 * No game payload or nonzero initializer is imported.
 */
#pragma force_active on

u8 lbl_8047AAF4[0x4];
u8 lbl_8047AAF0[0x4];
u8 lbl_8047AAEC[0x4];
u8 padding_8047AAEA[0x2];
u8 lbl_8047AAE8[0x2];
u8 lbl_8047AAE0[0x8];
u8 lbl_8047AAD8[0x8];
u8 lbl_8047AAD4[0x4];
u8 padding_8047AAD2[0x2];
u8 lbl_8047AAD0[0x2];
u8 lbl_8047AAC8[0x8];
u8 lbl_8047AAC4[0x4];
u8 lbl_8047AAC0[0x4];
u8 lbl_8047AABC[0x4];
u8 padding_8047AABA[0x2];
u8 lbl_8047AAB8[0x2];
u8 lbl_8047AAB4[0x4];
u8 lbl_8047AAB0[0x4];
u8 lbl_8047AAAC[0x4];
u8 padding_8047AAAA[0x2];
u8 lbl_8047AAA8[0x2];
u8 lbl_8047AAA0[0x8];
u8 padding_8047AA9D[0x3];
u8 lbl_8047AA9C;
u8 lbl_8047AA98[0x4];
u8 GSgfxVideoVsyncRate[0x4];
u8 padding_8047AA92[0x2];
u8 lbl_8047AA91;
u8 lbl_8047AA90;
u8 lbl_8047AA8C[0x4];
u8 lbl_8047AA88[0x4];
u8 padding_8047AA86[0x2];
u8 lbl_8047AA85;
u8 lbl_8047AA84;
u8 lbl_8047AA80[0x4];
u8 lbl_8047AA78[0x8];
u8 lbl_8047AA74[0x4];
u8 lbl_8047AA70[0x4];
u8 lbl_8047AA6C[0x4];
u8 padding_8047AA6A[0x2];
u8 lbl_8047AA68[0x2];
u8 padding_8047AA64[0x4];
u8 SamplingRate_8047AA60[0x4];

#pragma force_active reset

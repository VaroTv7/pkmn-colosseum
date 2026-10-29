/**
 * @file snd_sample_table.c
 * @brief REL 125 (common_rel): the sample-archive table.
 *
 * Module 125 .rodata 0xC54 - 0xD0C and .data 0x143918 - 0x1439D8. The
 * module's _prolog publishes the table through lbl_80478FB4 and its count
 * (8) through lbl_80478FB0. main.dol opens archive N with soundOpenWaveArchive:
 * GSsndOpenWaveDVD(N, path, 0, unk4, poolId, projId, sdirId).
 *
 * poolId/projId/sdirId are the member ids of the matching
 * snd_*_pool/_proj/_sdir files in common.fsys.
 */
#include "rel/common_rel.h"

/* Named literals preserve source-owned extents for object comparison.
 * Their contents and table references are unchanged; each starts at the
 * original four-byte boundary in the ProDG literal pool. */
const char lbl_125_rodata_C54[27] __attribute__((aligned(4))) = "/sound/snd_se_nakigoe.samp";
const char lbl_125_rodata_C70[26] __attribute__((aligned(4))) = "/sound/snd_se_motion.samp";
const char lbl_125_rodata_C8C[26] __attribute__((aligned(4))) = "/sound/snd_se_battle.samp";
const char lbl_125_rodata_CA8[28] __attribute__((aligned(4))) = "/sound/snd_music_atmos.samp";
const char lbl_125_rodata_CC4[28] __attribute__((aligned(4))) = "/sound/snd_se_nakigoe2.samp";
const char lbl_125_rodata_CE0[19] __attribute__((aligned(4))) = "/sound/snd_se.samp";
const char lbl_125_rodata_CF4[22] __attribute__((aligned(4))) = "/sound/snd_music.samp";

SndSampleArchive lbl_125_data_143918[8] = {
    { 1, 0, 0, 10, 0x01A50000, 0x01A60000, 0x01A80000, lbl_125_rodata_CF4 },
    { 1, 0, 0, 10, 0x01A50000, 0x01A60000, 0x01A80000, lbl_125_rodata_CF4 },
    { 1, 0, 6, 10, 0x01AD0000, 0x01AE0000, 0x01B00000, lbl_125_rodata_CE0 },
    { 0, 0, 9, 10, 0x01BD0000, 0x01BE0000, 0x01C00000, lbl_125_rodata_CC4 },
    { 0, 0, 1, 10, 0x01A90000, 0x01AA0000, 0x01AC0000, lbl_125_rodata_CA8 },
    { 0, 0, 5, 10, 0x01B10000, 0x01B20000, 0x01B40000, lbl_125_rodata_C8C },
    { 0, 0, 8, 10, 0x01B50000, 0x01B60000, 0x01B80000, lbl_125_rodata_C70 },
    { 0, 0, 4, 10, 0x01B90000, 0x01BA0000, 0x01BC0000, lbl_125_rodata_C54 },
};

/**
 * @file snd_song_table.c
 * @brief REL 125 (common_rel): the song table.
 *
 * Module 125 .rodata 0x56C - 0xC54 and .data 0x111B8C - 0x111E04. The
 * module's _prolog publishes the table through lbl_80478E34 and its count
 * (79) through lbl_80478E30. main.dol's sound code (fn_801653CC and its
 * neighbours) loads song N from its resource id, or from the path when the
 * id is 0 (retail has no such entry; entry 10 has neither).
 *
 * The ids use the FSYS member id format (file type 0x08).
 */
#include "rel/common_rel.h"

/* Named literals preserve source-owned extents for object comparison.
 * Their contents and table references are unchanged; each starts at the
 * original four-byte boundary in the ProDG literal pool. */
const char lbl_125_rodata_56C[22] __attribute__((aligned(4))) = "sound/ev_kinpaku.song";
const char lbl_125_rodata_584[19] __attribute__((aligned(4))) = "sound/gs_logo.song";
const char lbl_125_rodata_598[21] __attribute__((aligned(4))) = "sound/me_ex_tre.song";
const char lbl_125_rodata_5B0[21] __attribute__((aligned(4))) = "sound/me_winwin.song";
const char lbl_125_rodata_5C8[19] __attribute__((aligned(4))) = "sound/virtual.song";
const char lbl_125_rodata_5DC[23] __attribute__((aligned(4))) = "sound/siren_atmos.song";
const char lbl_125_rodata_5F4[20] __attribute__((aligned(4))) = "sound/level_up.song";
const char lbl_125_rodata_608[22] __attribute__((aligned(4))) = "sound/end_roll_c.song";
const char lbl_125_rodata_620[20] __attribute__((aligned(4))) = "sound/end_ev_2.song";
const char lbl_125_rodata_634[20] __attribute__((aligned(4))) = "sound/end_ev_1.song";
const char lbl_125_rodata_648[25] __attribute__((aligned(4))) = "sound/hyper_shiccho.song";
const char lbl_125_rodata_664[19] __attribute__((aligned(4))) = "sound/jyakira.song";
const char lbl_125_rodata_678[21] __attribute__((aligned(4))) = "sound/open_roll.song";
const char lbl_125_rodata_690[21] __attribute__((aligned(4))) = "sound/demo_roll.song";
const char lbl_125_rodata_6A8[21] __attribute__((aligned(4))) = "sound/fanfare03.song";
const char lbl_125_rodata_6C0[21] __attribute__((aligned(4))) = "sound/me_chukei.song";
const char lbl_125_rodata_6D8[21] __attribute__((aligned(4))) = "sound/miraclebo.song";
const char lbl_125_rodata_6F0[21] __attribute__((aligned(4))) = "sound/ev_shadow.song";
const char lbl_125_rodata_708[17] __attribute__((aligned(4))) = "sound/title.song";
const char lbl_125_rodata_71C[22] __attribute__((aligned(4))) = "sound/end_roll_b.song";
const char lbl_125_rodata_734[21] __attribute__((aligned(4))) = "sound/worldmap2.song";
const char lbl_125_rodata_74C[18] __attribute__((aligned(4))) = "sound/tretre.song";
const char lbl_125_rodata_760[23] __attribute__((aligned(4))) = "sound/battle9plus.song";
const char lbl_125_rodata_778[18] __attribute__((aligned(4))) = "sound/shinpi.song";
const char lbl_125_rodata_78C[19] __attribute__((aligned(4))) = "sound/battle8.song";
const char lbl_125_rodata_7A0[20] __attribute__((aligned(4))) = "sound/worldmap.song";
const char lbl_125_rodata_7B4[22] __attribute__((aligned(4))) = "sound/ev_shiccho.song";
const char lbl_125_rodata_7CC[21] __attribute__((aligned(4))) = "sound/ev_snatch.song";
const char lbl_125_rodata_7E4[19] __attribute__((aligned(4))) = "sound/battle9.song";
const char lbl_125_rodata_7F8[21] __attribute__((aligned(4))) = "sound/me_relive.song";
const char lbl_125_rodata_810[21] __attribute__((aligned(4))) = "sound/me_snatch.song";
const char lbl_125_rodata_828[18] __attribute__((aligned(4))) = "sound/me_win.song";
const char lbl_125_rodata_83C[19] __attribute__((aligned(4))) = "sound/battle6.song";
const char lbl_125_rodata_850[22] __attribute__((aligned(4))) = "sound/agb_shinka.song";
const char lbl_125_rodata_868[25] __attribute__((aligned(4))) = "sound/agb_me_shinka.song";
const char lbl_125_rodata_884[22] __attribute__((aligned(4))) = "sound/agb_fanfa5.song";
const char lbl_125_rodata_89C[19] __attribute__((aligned(4))) = "sound/dungeon.song";
const char lbl_125_rodata_8B0[21] __attribute__((aligned(4))) = "sound/mt_battle.song";
const char lbl_125_rodata_8C8[21] __attribute__((aligned(4))) = "sound/fanfare02.song";
const char lbl_125_rodata_8E0[21] __attribute__((aligned(4))) = "sound/fanfare01.song";
const char lbl_125_rodata_8F8[21] __attribute__((aligned(4))) = "sound/fanfare00.song";
const char lbl_125_rodata_910[23] __attribute__((aligned(4))) = "sound/agb_fanfa1b.song";
const char lbl_125_rodata_928[22] __attribute__((aligned(4))) = "sound/me_welcome.song";
const char lbl_125_rodata_940[18] __attribute__((aligned(4))) = "sound/me_fue.song";
const char lbl_125_rodata_954[24] __attribute__((aligned(4))) = "sound/tool_battle3.song";
const char lbl_125_rodata_96C[24] __attribute__((aligned(4))) = "sound/tool_battle2.song";
const char lbl_125_rodata_984[24] __attribute__((aligned(4))) = "sound/tool_battle1.song";
const char lbl_125_rodata_99C[22] __attribute__((aligned(4))) = "sound/tool_music.song";
const char lbl_125_rodata_9B4[24] __attribute__((aligned(4))) = "sound/me_undertime.song";
const char lbl_125_rodata_9CC[19] __attribute__((aligned(4))) = "sound/me_news.song";
const char lbl_125_rodata_9E0[21] __attribute__((aligned(4))) = "sound/darkside4.song";
const char lbl_125_rodata_9F8[19] __attribute__((aligned(4))) = "sound/battle5.song";
const char lbl_125_rodata_A0C[22] __attribute__((aligned(4))) = "sound/agb_me_asa.song";
const char lbl_125_rodata_A24[19] __attribute__((aligned(4))) = "sound/battle2.song";
const char lbl_125_rodata_A38[19] __attribute__((aligned(4))) = "sound/battle7.song";
const char lbl_125_rodata_A4C[23] __attribute__((aligned(4))) = "sound/chakumelo09.song";
const char lbl_125_rodata_A64[23] __attribute__((aligned(4))) = "sound/chakumelo08.song";
const char lbl_125_rodata_A7C[23] __attribute__((aligned(4))) = "sound/chakumelo07.song";
const char lbl_125_rodata_A94[23] __attribute__((aligned(4))) = "sound/chakumelo06.song";
const char lbl_125_rodata_AAC[23] __attribute__((aligned(4))) = "sound/chakumelo05.song";
const char lbl_125_rodata_AC4[23] __attribute__((aligned(4))) = "sound/chakumelo04.song";
const char lbl_125_rodata_ADC[23] __attribute__((aligned(4))) = "sound/chakumelo03.song";
const char lbl_125_rodata_AF4[23] __attribute__((aligned(4))) = "sound/chakumelo02.song";
const char lbl_125_rodata_B0C[23] __attribute__((aligned(4))) = "sound/chakumelo01.song";
const char lbl_125_rodata_B24[23] __attribute__((aligned(4))) = "sound/chakumelo00.song";
const char lbl_125_rodata_B3C[21] __attribute__((aligned(4))) = "sound/darkunder.song";
const char lbl_125_rodata_B54[18] __attribute__((aligned(4))) = "sound/gtsolo.song";
const char lbl_125_rodata_B68[20] __attribute__((aligned(4))) = "sound/mirrorbo.song";
const char lbl_125_rodata_B7C[27] __attribute__((aligned(4))) = "sound/wind_atmos_loop.song";
const char lbl_125_rodata_B98[17] __attribute__((aligned(4))) = "sound/saint.song";
const char lbl_125_rodata_BAC[19] __attribute__((aligned(4))) = "sound/pokecen.song";
const char lbl_125_rodata_BC0[20] __attribute__((aligned(4))) = "sound/darkside.song";
const char lbl_125_rodata_BD4[19] __attribute__((aligned(4))) = "sound/country.song";
const char lbl_125_rodata_BE8[18] __attribute__((aligned(4))) = "sound/stand2.song";
const char lbl_125_rodata_BFC[17] __attribute__((aligned(4))) = "sound/stand.song";
const char lbl_125_rodata_C10[21] __attribute__((aligned(4))) = "sound/watercity.song";
const char lbl_125_rodata_C28[21] __attribute__((aligned(4))) = "sound/windycity.song";
const char lbl_125_rodata_C40[20] __attribute__((aligned(4))) = "sound/null_bgm.song";

SndSong lbl_125_data_111B8C[79] = {
    { 0x019F0800, lbl_125_rodata_C40 },
    { 0x01A40800, lbl_125_rodata_C28 },
    { 0x01A20800, lbl_125_rodata_C10 },
    { 0x01A00800, lbl_125_rodata_BFC },
    { 0x01A10800, lbl_125_rodata_BE8 },
    { 0x01E30800, lbl_125_rodata_BD4 },
    { 0x01E20800, lbl_125_rodata_BC0 },
    { 0x01E50800, lbl_125_rodata_BAC },
    { 0x01E40800, lbl_125_rodata_B98 },
    { 0x01A30800, lbl_125_rodata_B7C },
    { 0x00000000, NULL },
    { 0x01E60800, lbl_125_rodata_B68 },
    { 0x01E70800, lbl_125_rodata_B54 },
    { 0x01E80800, lbl_125_rodata_B3C },
    { 0x02EE0800, lbl_125_rodata_B24 },
    { 0x02F10800, lbl_125_rodata_B0C },
    { 0x02F20800, lbl_125_rodata_AF4 },
    { 0x02F30800, lbl_125_rodata_ADC },
    { 0x02F40800, lbl_125_rodata_AC4 },
    { 0x02F50800, lbl_125_rodata_AAC },
    { 0x02F60800, lbl_125_rodata_A94 },
    { 0x02F70800, lbl_125_rodata_A7C },
    { 0x02F80800, lbl_125_rodata_A64 },
    { 0x02F90800, lbl_125_rodata_A4C },
    { 0x030A0800, lbl_125_rodata_A38 },
    { 0x03080800, lbl_125_rodata_A24 },
    { 0x03330800, lbl_125_rodata_A0C },
    { 0x05EF0800, lbl_125_rodata_9F8 },
    { 0x05F00800, lbl_125_rodata_9E0 },
    { 0x05F10800, lbl_125_rodata_9CC },
    { 0x05F20800, lbl_125_rodata_9B4 },
    { 0x06A40800, lbl_125_rodata_99C },
    { 0x06A10800, lbl_125_rodata_984 },
    { 0x06A20800, lbl_125_rodata_96C },
    { 0x06A30800, lbl_125_rodata_954 },
    { 0x06F10800, lbl_125_rodata_940 },
    { 0x06F20800, lbl_125_rodata_928 },
    { 0x06F00800, lbl_125_rodata_910 },
    { 0x08070800, lbl_125_rodata_8F8 },
    { 0x08080800, lbl_125_rodata_8E0 },
    { 0x08090800, lbl_125_rodata_8C8 },
    { 0x080A0800, lbl_125_rodata_8B0 },
    { 0x080F0800, lbl_125_rodata_89C },
    { 0x080B0800, lbl_125_rodata_884 },
    { 0x080C0800, lbl_125_rodata_868 },
    { 0x080D0800, lbl_125_rodata_850 },
    { 0x080E0800, lbl_125_rodata_83C },
    { 0x0B5A0800, lbl_125_rodata_828 },
    { 0x0B590800, lbl_125_rodata_810 },
    { 0x0B580800, lbl_125_rodata_7F8 },
    { 0x0B570800, lbl_125_rodata_7E4 },
    { 0x0BE80800, lbl_125_rodata_7CC },
    { 0x0BE70800, lbl_125_rodata_7B4 },
    { 0x0D120800, lbl_125_rodata_7A0 },
    { 0x0D110800, lbl_125_rodata_78C },
    { 0x0D600800, lbl_125_rodata_778 },
    { 0x0D5F0800, lbl_125_rodata_760 },
    { 0x0D710800, lbl_125_rodata_74C },
    { 0x0DAA0800, lbl_125_rodata_734 },
    { 0x0FED0800, lbl_125_rodata_71C },
    { 0x0FF00800, lbl_125_rodata_708 },
    { 0x0FEE0800, lbl_125_rodata_6F0 },
    { 0x0FEF0800, lbl_125_rodata_6D8 },
    { 0x0FF10800, lbl_125_rodata_6C0 },
    { 0x10810800, lbl_125_rodata_6A8 },
    { 0x10900800, lbl_125_rodata_690 },
    { 0x10A20800, lbl_125_rodata_678 },
    { 0x10A30800, lbl_125_rodata_664 },
    { 0x10B40800, lbl_125_rodata_648 },
    { 0x10B30800, lbl_125_rodata_634 },
    { 0x11140800, lbl_125_rodata_620 },
    { 0x11490800, lbl_125_rodata_608 },
    { 0x114A0800, lbl_125_rodata_5F4 },
    { 0x114C0800, lbl_125_rodata_5DC },
    { 0x114D0800, lbl_125_rodata_5C8 },
    { 0x114F0800, lbl_125_rodata_5B0 },
    { 0x114E0800, lbl_125_rodata_598 },
    { 0x119A0800, lbl_125_rodata_584 },
    { 0x12640800, lbl_125_rodata_56C },
};

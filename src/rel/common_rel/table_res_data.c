/**
 * @file table_res_data.c
 * @brief REL 125 (common_rel): the tableRes resource pointer table.
 *
 * Module 125 .data 0x8BCB4 - 0x8BCD4. _prolog publishes this table and
 * its eight-entry count for tableResBiosGetResPtr.
 *
 * shared_font_data.c and shared_message_data.c reuse definitions already
 * present in the DOL source for .data 0x2D2C-0x58044 and 0x647B4-0x76C94.
 * The other resources remain in dtk's original-object fallback, read from
 * the supplied common_rel.rel and not counted as source progress.
 */
#include "rel/common_rel.h"

extern u8 lbl_125_data_2D2C[];
extern u8 lbl_125_data_45A8C[];
extern u8 lbl_125_data_45A94[];
extern u8 lbl_125_data_494E4[];
extern u8 lbl_125_data_58044[];
extern u8 lbl_125_data_647B4[];
extern u8 lbl_125_data_76C94[];
extern u8 lbl_125_data_89CFC[];

void* lbl_125_data_8BCB4[8] = {
    lbl_125_data_2D2C,
    lbl_125_data_45A8C,
    lbl_125_data_45A94,
    lbl_125_data_494E4,
    lbl_125_data_58044,
    lbl_125_data_647B4,
    lbl_125_data_76C94,
    lbl_125_data_89CFC,
};

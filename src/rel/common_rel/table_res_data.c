/**
 * @file table_res_data.c
 * @brief REL 125 (common_rel): the tableRes resource pointer table.
 *
 * Module 125 .data 0x8BCB4 - 0x8BCD4. _prolog publishes this table and
 * its eight-entry count for tableResBiosGetResPtr.
 *
 * The resource payloads at .data 0x2D2C - 0x8BCB4, including fonts,
 * message tables and the remaining opaque resources, stay in dtk's
 * original-object fallback. They are read locally from the supplied
 * common_rel.rel; their bytes are not defined in this source file or
 * counted as compiled-source progress.
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

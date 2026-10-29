/**
 * @file shared_font_data.c
 * @brief Reuse the existing DOL font definitions in REL 125.
 *
 * Module .data 0x2D2C-0x58044 contains three fonts also defined in main.dol,
 * with an eight-byte font terminator between the first and second. Private
 * input hashes established equality of all three existing source ranges.
 * This view shares the definitions and emits no imports for pixel words.
 */
#define COMMON_REL_FONT_DATA
#include "../../game/data/data_8027A500.c"

typedef char SharedFontWordSize[(sizeof(void*) == 4 && sizeof(u32) == 4) ? 1 : -1];

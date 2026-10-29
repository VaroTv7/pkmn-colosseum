/**
 * @file shared_message_data.c
 * @brief Reuse the existing DOL message definition in REL 125.
 *
 * Module .data 0x647B4-0x76C94 is byte-identical to the existing
 * lbl_802CF810 definition. Select that definition without duplicating it
 * or importing the other DOL tables from the shared source owner.
 */
#define COMMON_REL_MESSAGE_DATA
#include "../../game/data/data_8027A500.c"

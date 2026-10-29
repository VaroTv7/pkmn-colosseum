/**
 * @file script_structure_89CFC.c
 * @brief GS VM bank header, function index, relocation index and zero globals.
 *
 * The complete resource spans .data 0x89CFC-0x8BCB4. This typed source owns
 * its first 156 bytes through 0x89D98. The adjacent 7,964 bytes are authored
 * in common_script_0596.json and compiled by tools/gs_vm_script_source.py.
 * Offsets retain the unchanged bank base; see docs/recon/common_script_0596.md.
 * Layout follows GSVMScript in include/game/gs_vm.h and cms_RegisterScript.
 * Every structural interval and the zero globals were hash-verified against
 * the private-input diagnostic. No script instructions or literals appear.
 */
#include "dolphin/types.h"

typedef struct RelScriptStructure {
    /* 0x00 */ u16 id;
    /* 0x02 */ u16 reserved02;
    /* 0x04 */ u16 functionCount;
    /* 0x06 */ u16 relocationCount;
    /* 0x08 */ u16 reserved08;
    /* 0x0A */ u8 relocated;
    /* 0x0B */ u8 reserved0B;
    /* 0x0C */ u32 relocationOffset;
    /* 0x10 */ s32 globalsOffset;
    /* 0x14 */ void* next;
    /* 0x18 */ u32 functionOffsets[27];
    /* 0x84 */ u32 relocationSites[1];
    /* 0x88 */ u32 globals[5];
} RelScriptStructure;

typedef char RelScriptStructureSize[(sizeof(RelScriptStructure) == 0x9C) ? 1 : -1];

RelScriptStructure lbl_125_data_89CFC __attribute__((aligned(4))) = {
    0x0596, 0x0101, 27, 1, 0x00C3, 0, 0, 0x84, 0x88, NULL,
    {
        197, 218, 239, 260, 667, 743, 849, 1531, 3685,
        3743, 337, 2197, 2346, 3479, 570, 156, 3917, 3983,
        4121, 5672, 4029, 4173, 3801, 3859, 7987, 8039, 4075,
    },
    { 6976 },
    { 0, 0, 0, 0, 0 },
};

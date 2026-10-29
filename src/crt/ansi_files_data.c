#include "dolphin/types.h"

/* MSL's standard streams. Layout is shared with stdio_range_800C7558.c and
 * exit.c; the initializer's fields and eighteen pointer relocations were
 * independently checked against the private-input data diagnostics. */
typedef struct MSLFileModes {
    u32 open_mode : 2;
    u32 io_mode : 3;
    u32 buffer_mode : 2;
    u32 file_kind : 3;
    u32 file_orientation : 2;
    u32 binary_io : 1;
} MSLFileModes;

typedef struct MSLFile {
    /* 0x00 */ u32 handle;
    /* 0x04 */ MSLFileModes file_mode;
    /* 0x08 */ u32 file_state;
    /* 0x0C */ u8 is_dynamically_allocated;
    /* 0x0D */ char char_buffer;
    /* 0x0E */ char char_buffer_overflow;
    /* 0x0F */ char ungetc_buffer[2];
    /* 0x12 */ u16 ungetc_wide_buffer[2];
    /* 0x18 */ u32 position;
    /* 0x1C */ u8* buffer;
    /* 0x20 */ u32 buffer_size;
    /* 0x24 */ u8* buffer_ptr;
    /* 0x28 */ u32 buffer_length;
    /* 0x2C */ u32 buffer_alignment;
    /* 0x30 */ u32 save_buffer_length;
    /* 0x34 */ u32 buffer_position;
    /* 0x38 */ void* position_fn;
    /* 0x3C */ void* read_fn;
    /* 0x40 */ void* write_fn;
    /* 0x44 */ u32 (*close_fn)(u32);
    /* 0x48 */ void* idle_fn;
    /* 0x4C */ struct MSLFile* next_file;
} MSLFile;

typedef char MSLFileSizeCheck[(sizeof(MSLFile) == 0x50) ? 1 : -1];

extern u8 lbl_803FFDF0[256];
extern u8 lbl_803FFCF0[256];
extern u8 lbl_803FFBF0[256];
extern u32 TRKCommSendWrite(u32 unused, u32 length, u32* address);
extern s32 __write_console(u32 handle, const void* data, u32* count, void* ref);
extern u32 __close_console(u32 handle);

/* stdin and stdout use line buffering; stderr is unbuffered. A closed fourth
 * record terminates the linked list used by __flush_all and __close_all. */
MSLFile __files[4] = {
    { 0, { 0, 1, 1, 2, 0, 0 }, 0, 0, 0, 0, { 0, 0 }, { 0, 0 },
      0, lbl_803FFDF0, 256, lbl_803FFDF0, 0, 0, 0, 0,
      NULL, (void*)TRKCommSendWrite, (void*)__write_console, __close_console,
      NULL, &__files[1] },
    { 1, { 0, 2, 1, 2, 0, 0 }, 0, 0, 0, 0, { 0, 0 }, { 0, 0 },
      0, lbl_803FFCF0, 256, lbl_803FFCF0, 0, 0, 0, 0,
      NULL, (void*)TRKCommSendWrite, (void*)__write_console, __close_console,
      NULL, &__files[2] },
    { 2, { 0, 2, 0, 2, 0, 0 }, 0, 0, 0, 0, { 0, 0 }, { 0, 0 },
      0, lbl_803FFBF0, 256, lbl_803FFBF0, 0, 0, 0, 0,
      NULL, (void*)TRKCommSendWrite, (void*)__write_console, __close_console,
      NULL, &__files[3] },
    { 0 }
};

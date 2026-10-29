#include "dolphin/types.h"
#include "dolphin/os/OSInterrupt.h"

/*
 * Zero-initialized storage at .sbss 0x8047A710-0x8047A760.
 * The preceding interrupt-handler pointer shares this owner so MWCC can
 * preserve the original eight-byte section alignment.
 * Original symbols establish object extents. Native scalar alignment supplies
 * ordinary gaps; remaining padding uses individual bytes. MWCC emits these
 * definitions in reverse order. Every symbol and gap is independently checked.
 */
#pragma force_active on

u8 lbl_8047A758[0x8];
u8 lbl_8047A750[0x8];
u8 lbl_8047A748[0x8];
u8 lbl_8047A744[0x4];
u8 lbl_8047A740[0x4];
u8 ResetFunctionQueue_8047A738[0x8];
u8 lbl_8047A730[0x8];
u8 lbl_8047A72C[0x4];
u8 lbl_8047A728[0x4];
u8 __OSLastInterruptTime[0x8];
u8 padding_8047A71C;
u8 padding_8047A71B;
u8 padding_8047A71A;
u16 __OSLastInterrupt;
u8 __OSLastInterruptSrr0[0x4];

__OSInterruptHandler* InterruptHandlerTable_8047A710;

#pragma force_active reset

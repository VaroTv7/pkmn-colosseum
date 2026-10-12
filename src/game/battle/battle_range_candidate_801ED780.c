/**
 * @file battle_range_candidate_801ED780.c
 * @brief Residual battle resource runtime candidate.
 *
 * Address range: 0x801ED780 - 0x801EE034.
 */

#include "dolphin/types.h"

#define FIELD_U8(base, off) (*(u8*)((u8*)(base) + (off)))
#define FIELD_U16(base, off) (*(u16*)((u8*)(base) + (off)))
#define FIELD_U32(base, off) (*(u32*)((u8*)(base) + (off)))
#define FIELD_F32(base, off) (*(f32*)((u8*)(base) + (off)))

extern u8 lbl_80314958[];
extern u8 lbl_80314C78[];
extern u8 lbl_80375230[];
extern u8 lbl_8046D630[];
extern u8 lbl_8047B5C0;
extern u8 lbl_8047B5C1;
extern u32 lbl_8047B5C4;
extern u32 lbl_8047B5C8;
extern f32 lbl_8047E4D0;
extern f32 lbl_8047E4D4;
extern f32 lbl_8047E4D8;
extern f32 lbl_8047E4DC;
extern f32 lbl_8047E4E0;
extern f32 lbl_8047E4E4;
extern f32 lbl_8047E4E8;
extern f32 lbl_8047E4EC;
extern f32 lbl_8047E4F0;
extern f64 lbl_8047E4F8;
extern f64 lbl_8047E500;

extern void* GScameraGetActiveCamera(void);
extern void GScameraGetPosition(void*, void*);
extern s32 GScolsys2Sun(void*, void*);
extern void* gfxWorldToScreen(void*, void*);
extern f32 vecMag(void*);
extern void gfxSetFlags(u32);
extern void gfxClearFlags(u32);
extern void gfxSetOrtho(f32, f32, f32, f32);
extern void gfxSetBlendMode(u32, u32, u32);
extern void gfxSetUpdates(u32, u32, u32);
extern void gfxSetZMode(u32, u32, u32);
extern void gfxSetCullMode(u32);
extern void fn_800D9ED8(u32);
extern void vecNormalize(void*, void*, f32);
extern u32 fn_800EF4FC(void*);
extern u32 fn_800EF4F4(void*);
extern void vecScale(void*, void*, f32);
extern void gfxLoadTexture(u32, void*);
extern void gfxBegin(u32);
extern void gfxVtxPos(f32, f32, f32);
extern void gfxVtxColor(u32, u32, u32, u32);
extern void gfxVtxTexCoord(f32, f32);
extern void gfxEnd(void);
extern void gfxSetPrimitive(u32);
extern void gfxSetVtxDesc(void*);

void flareDraw(void)
{
    f32 camera_pos[3];
    f32 col_pos[3];
    f32 delta[3];
    f32 span_ratio;
    f32 distance;
    f32 x0;
    f32 y0;
    f32 x1;
    f32 y1;
    u32 alpha;
    u32 task;
    u8* entry_list;
    u32* tex_table;
    u16 count;
    s32 mode;

    if (lbl_8047B5C0 == 0 || lbl_8047B5C1 == 0) {
        return;
    }

    task = (u32)GScameraGetActiveCamera();
    if (task == 0) {
        return;
    }

    GScameraGetPosition((void*)task, camera_pos);
    mode = GScolsys2Sun(lbl_80375230, camera_pos);
    if (mode == 1) {
        return;
    }

    mode = (s32)gfxWorldToScreen(lbl_80375230, col_pos);
    if (mode == 0) {
        return;
    }

    delta[0] = lbl_8047E4D0 - col_pos[0];
    delta[1] = lbl_8047E4D4 - col_pos[1];
    delta[2] = lbl_8047E4D8;
    distance = vecMag(delta);
    if ((distance > lbl_8047E4D8 ? distance : -distance) < lbl_8047E4DC) {
        return;
    }

    if (distance > (f32)FIELD_U32((void*)lbl_8047B5C4, 0x08)) {
        return;
    }

    gfxSetFlags(3);
    gfxClearFlags(4);
    gfxSetOrtho(lbl_8047E4D8, lbl_8047E4D8, lbl_8047E4E0, lbl_8047E4E4);
    gfxSetBlendMode(1, 1, 1);
    gfxSetUpdates(1, 1, 0);
    gfxSetZMode(0, 1, 1);
    gfxSetCullMode(0);
    fn_800D9ED8(1);

    if (mode == 2) {
        vecNormalize(delta, delta, distance);

        if (distance < (f32)FIELD_U32((void*)lbl_8047B5C4, 0x0C)) {
            span_ratio = lbl_8047E4E8;
        } else {
            f32 near_z = (f32)FIELD_U32((void*)lbl_8047B5C4, 0x0C);
            f32 far_z = (f32)FIELD_U32((void*)lbl_8047B5C4, 0x08);
            f32 range = far_z - near_z;

            span_ratio = (range - (distance - near_z)) / range;
            if (span_ratio < lbl_8047E4D8) {
                span_ratio = lbl_8047E4D8;
            } else if (span_ratio > lbl_8047E4E8) {
                span_ratio = lbl_8047E4E8;
            }
        }

        alpha = (u32)(lbl_8047E4EC * span_ratio);
        gfxSetPrimitive(4);
        gfxSetVtxDesc(lbl_80314C78);

        entry_list = (u8*)lbl_8047B5C8;
        tex_table = (u32*)lbl_8046D630;
        count = FIELD_U16((void*)lbl_8047B5C4, 0x06);

        while (count-- != 0) {
            void* tex = (void*)tex_table[(u32)FIELD_U16(entry_list, 0x02)];

            if (FIELD_U8(entry_list, 0x00) == 1) {
                x0 = col_pos[0] - FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4FC(tex);
                y0 = col_pos[1] - FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4F4(tex);
                x1 = col_pos[0] + FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4FC(tex);
                y1 = col_pos[1] + FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4F4(tex);
            } else {
                vecScale(&delta[0], &delta[0], lbl_8047E4F0 * FIELD_F32(entry_list, 0x04) * distance);
                x0 = lbl_8047E4D0 + delta[0] - FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4FC(tex);
                y0 = lbl_8047E4D4 + delta[1] - FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4F4(tex);
                x1 = lbl_8047E4D0 + delta[0] + FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4FC(tex);
                y1 = lbl_8047E4D4 + delta[1] + FIELD_F32(entry_list, 0x08) * (f32)fn_800EF4F4(tex);
            }

            gfxLoadTexture(0, tex);
            gfxBegin(4);

            gfxVtxPos(x0, y0, lbl_8047E4D8);
            gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
            gfxVtxTexCoord(lbl_8047E4D8, lbl_8047E4D8);

            gfxVtxPos(x1, y0, lbl_8047E4D8);
            gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
            gfxVtxTexCoord(lbl_8047E4E8, lbl_8047E4D8);

            gfxVtxPos(x0, y1, lbl_8047E4D8);
            gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
            gfxVtxTexCoord(lbl_8047E4D8, lbl_8047E4E8);

            gfxVtxPos(x1, y1, lbl_8047E4D8);
            gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
            gfxVtxTexCoord(lbl_8047E4E8, lbl_8047E4E8);
            gfxEnd();

            entry_list += 0x0C;
        }

        if (distance >= (f32)FIELD_U32((void*)lbl_8047B5C4, 0x0C)) {
            return;
        }

        if (distance < (f32)FIELD_U32((void*)lbl_8047B5C4, 0x10)) {
            span_ratio = FIELD_F32((void*)lbl_8047B5C4, 0x14);
        } else {
            f32 near_z = (f32)FIELD_U32((void*)lbl_8047B5C4, 0x10);
            f32 far_z = (f32)FIELD_U32((void*)lbl_8047B5C4, 0x0C);
            f32 range = far_z - near_z;

            span_ratio = FIELD_F32((void*)lbl_8047B5C4, 0x14) * ((range - (distance - near_z)) / range);
            if (span_ratio < lbl_8047E4D8) {
                span_ratio = lbl_8047E4D8;
            } else if (span_ratio > lbl_8047E4E8) {
                span_ratio = lbl_8047E4E8;
            }
        }

        alpha = (u32)(lbl_8047E4EC * span_ratio);
        gfxClearFlags(2);
        gfxSetPrimitive(4);
        gfxSetVtxDesc(lbl_80314958);
        gfxBegin(4);

        gfxVtxPos(lbl_8047E4D8, lbl_8047E4D8, lbl_8047E4D8);
        gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
        gfxVtxPos(lbl_8047E4E0, lbl_8047E4D8, lbl_8047E4D8);
        gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
        gfxVtxPos(lbl_8047E4D8, lbl_8047E4E4, lbl_8047E4D8);
        gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
        gfxVtxPos(lbl_8047E4E0, lbl_8047E4E4, lbl_8047E4D8);
        gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
        gfxEnd();
        return;
    }

    gfxSetBlendMode(2, 1, 1);

    if (distance >= (f32)FIELD_U32((void*)lbl_8047B5C4, 0x0C)) {
        return;
    }

    if (distance < (f32)FIELD_U32((void*)lbl_8047B5C4, 0x10)) {
        span_ratio = FIELD_F32((void*)lbl_8047B5C4, 0x18);
    } else {
        f32 near_z = (f32)FIELD_U32((void*)lbl_8047B5C4, 0x10);
        f32 far_z = (f32)FIELD_U32((void*)lbl_8047B5C4, 0x0C);
        f32 range = far_z - near_z;

        span_ratio = FIELD_F32((void*)lbl_8047B5C4, 0x18) * ((range - (distance - near_z)) / range);
        if (span_ratio < lbl_8047E4D8) {
            span_ratio = lbl_8047E4D8;
        } else if (span_ratio > lbl_8047E4E8) {
            span_ratio = lbl_8047E4E8;
        }
    }

    alpha = (u32)(lbl_8047E4EC * span_ratio);
    gfxClearFlags(2);
    gfxSetPrimitive(4);
    gfxSetVtxDesc(lbl_80314958);
    gfxBegin(4);

    gfxVtxPos(lbl_8047E4D8, lbl_8047E4D8, lbl_8047E4D8);
    gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
    gfxVtxPos(lbl_8047E4E0, lbl_8047E4D8, lbl_8047E4D8);
    gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
    gfxVtxPos(lbl_8047E4D8, lbl_8047E4E4, lbl_8047E4D8);
    gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
    gfxVtxPos(lbl_8047E4E0, lbl_8047E4E4, lbl_8047E4D8);
    gfxVtxColor(0, alpha & 0xFF, alpha & 0xFF, alpha & 0xFF);
    gfxEnd();
}

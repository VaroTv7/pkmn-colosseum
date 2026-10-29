# Battle and purification small-data reconstruction

These source owners reconstruct 154 bytes of the previously original-backed
`.sdata` interval `0x80478D08..0x80478DB4`:

| Owner | Interval | Bytes |
| --- | --- | ---: |
| `src/game/data/sdata_80478D08.c` | `0x80478D08..0x80478D86` | 126 |
| `src/game/data/sdata_80478D98.c` | `0x80478D98..0x80478DB4` | 28 |

The 18 bytes at `0x80478D86..0x80478D98` retain their original-object fallback.
Their map labels are `lbl_80478D86`, `lbl_80478D88` and `lbl_80478D8C`.
No initializer is inferred from an unrelated short byte match.

## Evidence and validation boundary

The reconstruction uses existing C consumers, typed table layouts and the
metadata-only target hashes from CI5 (`2d9ab305`). No original payload bytes
were read or copied. Every one of the 22 reconstructed original symbols matches
its complete preexisting SHA-256, including any zero padding included in its
old extent. The three intervening hidden flag gaps also match their all-zero
hashes. The version pointer has one `R_PPC_ADDR32` relocation to
`lbl_803751F0`, with addend zero; its encoded word is zero before relocation.

This is source-model evidence. Acceptance still requires the pinned compiler
to reproduce the actual sections, symbol placements and relocation, followed
by the normal code-identity and canonical-link gates. The source models predict:

| Interval | Pre-relocation SHA-256 |
| --- | --- |
| `0x80478D08..0x80478D86` | `d6498c304a380ef0ca254ad2b76d61759e24aaa2b29145a73ece3145d1c6ed68` |
| `0x80478D98..0x80478DB4` | `fccf313e5a55cb7dd8c680590df9c563a5a8b1fe1ef01846ef25fa6a59e18a9b` |

## Typed values

The address suffix identifies each existing `lbl_80478...` symbol.

| Suffix | Source type and initializer | Existing evidence |
| --- | --- | --- |
| `D08` | `char* = lbl_803751F0` | `THPInit` passes the pointer to `OSRegisterVersion`; target relocation identifies the same string. |
| `D10` | `u16 = 21 * 2` | `fightPreloadResources` advances two halfwords per archive/result pair; `lbl_803752A0` has 21 live pairs. |
| `D18` | `u8 = 5` | `fightActionFlowKaisiPreSubLoad` uses this random-index bound for the five nonzero IDs in `lbl_80375970`. |
| `D20` | `u32 = 11` | `fightEncountWipeDataBiosGetPtr` indexes eleven 12-byte wipe records. |
| `D28` | `u32 = 8` | The condition accessors index eight 24-byte `ColosseumEventPairRow` records. |
| `D30` | One zero `ColosseumEventRow6` | `joukenDataGet0`, `joukenDataGet2` and `joukenDataGet4` read its byte/halfword fields with six-byte row stride. |
| `D38` | `u32 = 1` | Bounds check for that one event row. |
| `D40` | `u32 = 30` | `fightTargetDataBiosGetPtr` indexes thirty eight-byte records in `lbl_80375AC8`. |
| `D48` | `u32 = 20` | `fightActionKindDataBiosGetPtr` indexes the twenty typed action records in `lbl_80375BB8`. |
| `D50` | `u32 = 2` | `fightKoukaDataBiosGetPtr` indexes two six-byte effect records in `lbl_80375CB8`. |
| `D58` | `u8[5] = {16, 8, 4, 3, 2}` | `fightWazaCriticalDataBiosGetBunbo` reads a byte denominator; the caller clamps the stage to the table bound. The complete eight-byte mapped extent verifies the five-stage denominator hypothesis and its padding. |
| `D60` | `u32 = 5` | Bounds and clamping for those five denominator entries. |
| `D68` | `u32 = 13` | `fightAbicntDoKakeWaru` indexes the thirteen nonpadding numerator/denominator pairs in `lbl_80375D10`. |
| `D70` | `u32 = 13` | `fightWazaHitKakurituDataBiosGetPtr` indexes the thirteen nonpadding pairs in `lbl_80375DD0`. |
| `D78`, `D7B`, `D7D` | Zero flag bytes | Battle script code clears the eight-byte flag block and addresses its existing sublabels at offsets 0, 3 and 5. |
| `D80` | `u16[3] = {0x45, 0x43, 0x40}` | Script `lbl_80377B0C` passes the first halfword to `WS_STATUS_SET16`; other scripts use `D80+2`. Opcode `0xFC` and status kind 7 route these operands to `fightFloorSetStatus` field `0x3B`. The same three values occur in direct C setters of that field; the six-byte hash selects their order. |
| `D98` | `s32 = 4 * 6` | `toolentryDebugPokemonCreate` allocates/counts this many Pokemon and initializes four parties of six. Complete extent verification confirms the capacity is 24. |
| `DA0` | `u16[2] = {100, 3}` | `std244_spawnEffectAtPosition` passes one pair to `effectCreate` and `effectPlayWaza`. |
| `DA8` | `u16[4] = {77, 4, 122, 4}` | `reliveMain` passes two pairs to `loadSequence` and `effectPlayWaza`. |
| `DB0` | `u16[2] = {122, 4}` | The purification ceremony and move-forgetting callback pass one pair to the same consumers. |

The sequence IDs were recovered as typed `(group, type)` pairs. Both consumers
advance a `u16*` by two elements per pair. `fn_801DDEE4` explicitly accepts
types 1 through 4, with nonzero group IDs below the existing source-backed
counts 364 for types 1 through 3 and 219 for type 4. Comparing complete symbol
hashes across that finite valid domain selects the listed pairs uniquely.
This does not reuse opaque bytes from an unrelated compiled source object.

The source evidence is in:

- `src/dolphin/thp/THP_range_801E1B54.c`
- `src/game/battle/battle_main.c`
- `src/game/fight_action.c` and `fight_action_exact_8020D784.c`
- `src/game/fight_encount_exact_8020DD44.c`
- `src/game/fight_kouka_exact_8020D968.c`
- `src/game/fight_out_pokemon_exact_802096E8.c`
- `src/game/fight_target.c`, `fight_trainer.c` and `fight_seq.c`
- `src/game/fight_range_80211A00.c`, `status.c` and `fight_floor.c`
- `src/game/toolentry.c`, `pokemon_relive.c` and `sequence.c`
- `src/game/data/data_80375230.c`, `data_80375938.c`, `data_80377B0C.c`,
  `data_80379714.c`, `rodata_80279B78.c` and `sdata_80478CA8.c`

## Scalar extents and padding

Sixteen old map entries include padding beyond the active type demonstrated
by their consumers. Their symbol extents are refined to the active object size;
the same bytes remain owned by the same section, and address-named source
padding retains the independently verified zero storage. Neither section
coverage nor the total-data denominator changes.

| Symbols | Old size | Active source size |
| --- | ---: | ---: |
| `D08`, `D20`, `D28`, `D38`, `D40`, `D48`, `D50`, `D60`, `D68`, `D70`, `D98`, `DA0` | 8 | 4 |
| `D10` | 8 | 2 |
| `D18` | 8 | 1 |
| `D30` | 8 | 6 |
| `D58` | 8 | 5 |

Explicit padding arrays use the compiler-verified one-byte alignment attribute
to avoid adding a second alignment gap. Every definition is explicitly placed
in `.sdata`, including zero-initialized records and flags, and retained through
the scoped main export list. No original symbols are renamed.

## Unresolved interval

The existing source contains no typed direct reference to `D86`, `D88` or
`D8C`. A scan of the existing C bytecode initializers found the `D80+2`
references described above, but no encoded pointer into `D86..D98`. Their map
sizes or generic data-format hints alone do not establish defensible source
semantics. These 18 bytes therefore remain an explicit unresolved interval.

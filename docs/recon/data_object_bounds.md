# Data object extents and consumer bounds

The source audit after CI8 found seven new definitions whose mapped extents
were smaller than the actual objects accessed by existing compiled consumers.
Matching native bytes and addresses did not establish valid C object bounds.
These corrections preserve every address and the complete physical data
denominator. CI9 verifies the corrected native source owners, all 26 canonical
outputs and direct comparisons, all 34 zero-data layouts, and unchanged
function identities and physical coverage. The verified source revision is
`dcdfc947cd77221ff38159679f07e704be77d9e4`; the report and final PR-check status
are recorded in [`DATA_MATCHING.md`](../DATA_MATCHING.md).

## Proven complete object extents

| Object | Previous source extent | Correct extent | Existing source evidence |
| --- | ---: | ---: | --- |
| `lbl_804788C8` | Two bytes | `s16[2]`, four bytes | `game/menu/pda_exact_800492CC_gc20.c` declares two coordinates and reads/writes indices 0 and 1. |
| `lbl_8047AD04` | One byte | `u8[4]`, four bytes | `game/menu_exact_801038F8.c` and `game/menu_exact_80103BA8.c` iterate over all four controller ports and read/write each array element. |
| `lbl_8047A60C` | One byte | `u32`, four bytes | `game/menu/pkjb_exact_80073990.c` compares the complete boot key through the `u32` declaration in `game/menu/pkjb_uploader_shared.h`; the existing uploader implementation also copies and updates four bytes. |

The C8 array absorbs the separately named zero halfword at CA. The AD04 and
A60C definitions absorb their previously unnamed three-byte zero gaps. No
other mapped object intersects those gaps. C8's four bytes independently hash
to the all-zero four-byte value in the CI8 symbol/gap metadata; the other two
objects occupy existing NOBITS storage. The three map sizes are refined to
four bytes. `verify_zero_data_layout.py` derives the two updated BSS expectations
and remaining gaps directly from that map, preserving each complete section
extent. The obsolete CA padding export is removed.

All active consumers of C8 and AD04 already declare the complete arrays.
The A60C consumers declare the four-byte scalar. Their function source does
not need to change for these corrections.

## Complete arrays with interior mapped names

`lbl_804788CC` and `lbl_804788D0` are two-element coordinate arrays in the same
PDA renderer. Their second elements are nonzero and have mapped names
`lbl_804788CE` and `lbl_804788D2`. Those names are retained. Defining the first
element as a separate scalar or one-element array would leave accesses to
element 1 outside the C object. There is no verified source alias mechanism
for these interior labels, so CC through D8 remains original fallback. This
12-byte interval includes the following four-byte D4 lookup table so the next
compiled source section begins at its original eight-byte-aligned D8 address.

The four-port mask and port-order tables at `lbl_80478950` and `lbl_80478954`
are each four-byte arrays. `game/menu/cardesavedata.c` declares these sizes and
reads all four entries, including an explicit loop from zero through three.
The mapped names at 951 and 955 split those arrays after their first byte.
The complete eight-byte interval 950 through 958 therefore also remains
original fallback, retaining all four original symbol names.

| Interval | Bytes | Ownership |
| --- | ---: | --- |
| `0x80478820..0x804788CC` | 172 | Compiled `sdata_80478820.c` |
| `0x804788CC..0x804788D8` | 12 | Original fallback; explicit four-byte boundary alignment |
| `0x804788D8..0x80478950` | 120 | Compiled `sdata_804788D8.c` |
| `0x80478950..0x80478958` | 8 | Original fallback |
| `0x80478958..0x80478970` | 24 | Compiled `sdata_80478958.c` |

The same 336 physical bytes remain in scope. CI9 verifies all 316 source-owned
bytes as exact and source-linked: 172, 120 and 24 bytes from the three compiled
owners. The other 20 bytes remain fallback and receive no source credit.
Every remaining initializer is unchanged from the CI8-verified source except
the C8 array's truthful extent refinement. No original object payload is copied
into a source initializer. The corrected AD04 and A60C extents also pass the
strict native zero-layout checks.

The SDK literal/state additions and the 152-byte initialized-zero owner have
no concrete consumer-bound conflict in this targeted audit. This audit checks
actual declarations and uses; it does not replace the native layout, canonical
output, relocation, or full function-identity checks. CI9 supplies those
checks for this source revision. The later documentation/topology refresh must
still pass the final required checks on PR #663.

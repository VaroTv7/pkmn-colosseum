# Initialized zero storage at 0x8038FF64

`src/game/data/data_8038FF64.c` reconstructs the 152-byte `.data` interval
`0x8038FF64..0x8038FFFC` with explicit zero initializers. The existing symbol
map supplies the three object names and extents. The complete CI6 target
metadata verifies that every object and the intervening/trailing storage are
zero, and that the section contains no relocations.

| Existing symbol or gap | Address | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `lbl_8038FF64` | `0x8038FF64` | 18 | `60daa3a5f7dbfa200f8c82840ecf5b42640b70f3b7218a4c6bbd67db542e75a4` |
| `lbl_8038FF76` | `0x8038FF76` | 131 | `d367e8be9eb342df9fd9f890c99b1a955f774f74183a2adf81b238bcb9527c05` |
| `lbl_8038FFF9` | `0x8038FFF9` | 1 | `6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d` |
| Trailing gap, named `padding_8038FFFA` in source | `0x8038FFFA` | 2 | `96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7` |

The complete section SHA-256 is
`85ada57e1f601e962d705f389285adb4e74f450bc00672240dfef7399d82457f`.
Hashing independently generated zero storage at these recorded lengths
reproduces every value above. No original payload or unrelated compiled data
is used to generate the definitions. No runtime meaning, field structure or
script semantics is assigned to these address-named objects.

## Native layout guard

Every object retains its existing name, size and offset. Byte alignment on
the last two mapped objects preserves the offsets 18 and 149; the final
two-byte zero object occupies only the independently verified gap. Explicit
array initializers and `-sdata 0` follow the existing compiler-verified pattern
for initialized zero data. All four source definitions are retained through
the scoped source export list.

The retail section begins four bytes past an eight-byte boundary. The
`data_alignment=4` link view therefore runs the strict existing
`tools/source_object_metadata.py align` guard. Before lowering section
alignment, it requires one initialized data-only section, complete byte
equality, identical original object extents and relocation semantics, complete
coverage by original symbols plus verified zero gaps, and compiler-required
alignment of at most four for every real object. It does not copy target
payload or modify symbol offsets/sizes. Native source remains the report
input.

This check matters because all-zero bytes alone would conceal reordered or
shifted objects. Source compilation, the guarded link view, linked-address
diagnostics and canonical output verification must all pass before accepting
the 152 bytes as source-owned progress. The entire interval stays in the full
physical data denominator.

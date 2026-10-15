# Dolphin SDK reset assembly

## Reset_8009FF50

- Origin: Nintendo Dolphin SDK OSReset.c, the hardware-reset primitive at
  Colosseum GC6E01 address 0x8009FF50. The imported implementation comes from
  donor commit f559f0cc143ffb11b87eeb48f903d5fac51d644a.
- Why it cannot be C: this is the SDK's frameless hardware-reset sequence,
  using HID0 special-register access, isync/sync and raw time-base reads, then
  writing the reset registers and looping without a normal return. Ordinary
  portable C does not express those processor operations or the frameless
  entry convention. This identifies the assembly contract, not a proof that
  every compiler-specific C extension has been exhausted.
- Other decompilations: zeldaret/tww retains the same Reset body as an ASM
  function, including the HID0 update, time-base delay threshold 0x1124,
  reset-register stores, and branch structure:
  https://github.com/zeldaret/tww/blob/f5234ec8f4b8f4119b8db4a018c1ca25572988b1/src/dolphin/os/OSReset.c
- External branch targets: none; every branch is local to the function.

The registry entry is restricted to this source path, function, and exact
mnemonic set. It does not expand the generic hardware-primitives allowlist.
No instruction was changed by registration. Quality tests exercise the full
body, reject an added call, and reject reusing this permission in game code.
Fresh retail-byte validation remains a separate requirement; the historical
source comparison alone is not a new matching measurement.

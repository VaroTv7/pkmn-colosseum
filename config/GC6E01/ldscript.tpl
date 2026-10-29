MEMORY
{
    text : origin = $ORIGIN
}

SECTIONS
{
    GROUP:
    {
        $SECTIONS
        .stack ALIGN(0x100):{}
    } > text

    /* Preserve the retail vector-table end label at the first tail helper. */
    gTRKInterruptVectorTableEnd = fn_800053E0;

    _stack_end = $LAST_SECTION_SYMBOL + SIZEOF($LAST_SECTION_NAME);
    _stack_addr = (_stack_end + $STACKSIZE + 0x7) & ~0x7;
    _db_stack_addr = (_stack_addr + 0x8000);
    _db_stack_end = _stack_addr;
    __ArenaLo = (_db_stack_addr + 0x1f) & ~0x1f;
    __ArenaHi = $ARENAHI;
}

FORCEACTIVE
{
    $FORCEACTIVE
}

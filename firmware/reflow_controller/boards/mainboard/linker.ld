ENTRY(Reset_Handler)

MEMORY
{
  /* BTT's LPC1769 bootloader occupies the first 16 KiB of internal flash. */
  FLASH (rx) : ORIGIN = 0x00004000, LENGTH = 496K

  /*
   * LPC1769 has additional AHB SRAM banks. Phase 1 uses only the contiguous
   * 32 KiB local SRAM region; later drivers may declare explicit AHB sections.
   */
  RAM (rwx) : ORIGIN = 0x10000000, LENGTH = 32K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
  .isr_vector : {
    . = ALIGN(4);
    KEEP(*(.isr_vector))
  } > FLASH

  .text : {
    . = ALIGN(4);
    *(.text*)
    *(.rodata*)
    . = ALIGN(4);
    _etext = .;
  } > FLASH

  .data : {
    . = ALIGN(4);
    _sdata = .;
    _sidata = LOADADDR(.data);
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } > RAM AT > FLASH

  .bss (NOLOAD) : {
    . = ALIGN(4);
    _sbss = .;
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
  } > RAM
}

#ifndef __FLASH_ONBOARD_H__
#define __FLASH_ONBOARD_H__

#include "pico/stdlib.h"
#include "hardware/flash.h"

#ifndef PICO_FLASH_STORAGE_SIZE
#define PICO_FLASH_STORAGE_SIZE FLASH_SECTOR_SIZE
#endif

// PICO_FLASH_STORAGE_SIZE must be a multiple of 4096 bytes (one sector)
#if PICO_FLASH_STORAGE_SIZE % FLASH_SECTOR_SIZE != 0
#error Flash storage size not set to a multiple of FLASH_SECTOR_SIZE (4096  bytes)
#endif

#ifndef FLASH_STORAGE_START
#define FLASH_STORAGE_START (PICO_FLASH_SIZE_BYTES - (PICO_FLASH_STORAGE_SIZE * 2))
#endif // FLASH_STORAGE_START

// CRC is at end of storage and is 2 bytes long
#define FLASH_STORAGE_MEMORY_CRC_LOCATION ((XIP_BASE + FLASH_STORAGE_START + PICO_FLASH_STORAGE_SIZE) - 2)

// This is the address of our storage in RP2040 memory space (not flash offset space)
#define FLASH_STORAGE_MEMORY_ADDR (XIP_BASE + FLASH_STORAGE_START)

uint16_t flash_get_storage_crc();
uint16_t flash_get_calculated_crc();
uint8_t flash_valdate_crc();
uint8_t flash_storage_init(uint8_t disableInterrupts);
uint8_t flash_storage_init_if_needed(uint8_t disableInterrupts);

#endif // __FLASH_ONBOARD_H__
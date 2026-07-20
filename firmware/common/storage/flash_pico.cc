#include <string.h>

#include "pico/multicore.h"
#include "hardware/flash.h"
#include "hardware/sync.h"

#include "../utils/crc16.h"
#include "../utils/core_sync.h"
#include "flash_pico.h"

uint16_t flash_get_storage_crc()
{
    // Get pointer to storage buffer
    uint8_t *flash_data = (uint8_t *)FLASH_STORAGE_MEMORY_ADDR;

    // Confirm CRC on current state
    return *((uint16_t *)(FLASH_STORAGE_MEMORY_CRC_LOCATION));
}

uint16_t flash_get_calculated_crc()
{
    // Get pointer to storage buffer
    uint8_t *flash_data = (uint8_t *)FLASH_STORAGE_MEMORY_ADDR;
    return crc16_buffer(~0, flash_data, PICO_FLASH_STORAGE_SIZE - 2);
}

uint8_t flash_valdate_crc()
{
    // Confirm CRC on current state
    uint16_t calculated_crc = flash_get_calculated_crc();
    uint16_t storage_crc = flash_get_storage_crc();

    // Make sure CRC matches
    uint8_t crc_ok = calculated_crc == storage_crc;
    return crc_ok;
}

uint8_t flash_storage_init(uint8_t disableInterrupts)
{
    uint32_t saved_interrupt_state;
    if (disableInterrupts)
    {
        // Reset core 1, we will restart it after writing the flash
        multicore_reset_core1();
        saved_interrupt_state = save_and_disable_interrupts();
    }

    // flash_range_erase(FLASH_STORAGE_START, PICO_FLASH_STORAGE_SIZE);

    // Construct in memory copy
    static uint8_t flash_data[PICO_FLASH_STORAGE_SIZE];

    // Clear data
    memset(flash_data, 0, PICO_FLASH_STORAGE_SIZE);

    // Calc CRC
    uint16_t crc = crc16_buffer(~0, flash_data, PICO_FLASH_STORAGE_SIZE - 2);

    // Set CRC in data that is to be written
    uint16_t *flash_crc = (uint16_t *)(&flash_data[PICO_FLASH_STORAGE_SIZE - 2]);
    *flash_crc = crc;

    // Write to flash
    flash_range_program(FLASH_STORAGE_START, flash_data, PICO_FLASH_STORAGE_SIZE);

    if (disableInterrupts)
    {
        restore_interrupts(saved_interrupt_state);
    }

    return flash_valdate_crc();
}

uint8_t flash_storage_init_if_needed(uint8_t disableInterrupts)
{
    // Make sure CRC matches
    bool crc_ok = flash_valdate_crc();

    if (!crc_ok)
    {
        return flash_storage_init(disableInterrupts);
    }

    // Return true if was OK, false otherwise
    return crc_ok;
}
#ifndef __CORE_SYNC_H__
#define __CORE_SYNC_H__

#include "pico/stdlib.h"

void core_sync_init();
uint32_t core_sync_get_lock_num();
uint32_t core_sync_lock();
void core_sync_unlock(uint32_t status);
void core_sync_set_code(uint8_t code);
void core_sync_wait_block_code(uint8_t code);
bool core_sync_wait_noblock_code(uint8_t code);
void core_sync_set_code_wait_block(uint8_t set_code, uint8_t wait_code);

#endif // __CORE_SYNC_H__
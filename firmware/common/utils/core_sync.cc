#include "hardware/sync.h"

#include "core_sync.h"
#include "intercore_queue.h"

// Get and hold on to the spin lock
uint32_t core_sync_lock_num;

uint8_t core_sync_code;

void core_sync_init()
{
    core_sync_lock_num = spin_lock_claim_unused(true);
}

uint32_t core_sync_get_lock_num()
{
    return core_sync_lock_num;
}

uint32_t core_sync_lock()
{
    return spin_lock_blocking(spin_lock_instance(core_sync_lock_num));
}

void core_sync_unlock(uint32_t status)
{
    spin_unlock(spin_lock_instance(core_sync_lock_num), status);
}

void core_sync_set_code(uint8_t code)
{
    uint32_t save = core_sync_lock();
    core_sync_code = code;
    core_sync_unlock(save);
}

void core_sync_wait_block_code(uint8_t code)
{
    bool code_found = false;
    while (true)
    {
        uint32_t save = core_sync_lock();

        if (core_sync_code == code)
        {
            code_found = true;

            // Reset the code
            core_sync_code = Q_MT_NONE;
        }

        core_sync_unlock(save);

        if (code_found == true)
        {
            break;
        }

        // Give other core chance to lock the code
        busy_wait_us_32(5000);
    }
}

bool core_sync_wait_noblock_code(uint8_t code)
{
    bool code_found = false;
    uint32_t save = core_sync_lock();

    if (core_sync_code == code)
    {
        code_found = true;

        // Reset the code
        core_sync_code = Q_MT_NONE;
    }

    core_sync_unlock(save);

    return code_found;
}

void core_sync_set_code_wait_block(uint8_t set_code, uint8_t wait_code)
{
    core_sync_set_code(set_code);
    core_sync_wait_block_code(wait_code);
}

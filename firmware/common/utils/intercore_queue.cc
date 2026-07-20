#include "pico/util/queue.h"
#include "hardware/pio.h"

#include "debug.h"
#include "intercore_queue.h"

queue_t interprocess_queue;

typedef struct interprocess_queue_message
{
    uint8_t message;
} interprocess_queue_message_t;

void intercore_queue_init()
{
    queue_init_with_spinlock(&interprocess_queue, sizeof(interprocess_queue_message_t), 10, next_striped_spin_lock_num());
}

uint8_t intercore_queue_block_message()
{
    // Remove from queue
    interprocess_queue_message_t q_item;
    queue_remove_blocking(&interprocess_queue, &q_item);

    return q_item.message;
}

bool intercore_queue_try_add_message(uint8_t message)
{
    interprocess_queue_message_t q_item;
    q_item.message = message;
    return queue_try_add(&interprocess_queue, &q_item);
}

void intercore_queue_add_message(uint8_t message)
{
    interprocess_queue_message_t q_item;
    q_item.message = message;
    queue_add_blocking(&interprocess_queue, &q_item);
}

uint8_t intercore_queue_wait_message(uint8_t message)
{
    interprocess_queue_message_t q_item;

    // Wait for a message
    while (true)
    {
        if (!queue_try_peek(&interprocess_queue, &q_item))
        {
            continue;
        }

        // Is the pending messsage the message we are waiting for?
        if (q_item.message == message)
        {
            // Remove the message and exit loop
            queue_remove_blocking(&interprocess_queue, &q_item);
            return q_item.message;
        }
        else
        {
            while (true)
            {
                // Expected
                flash_code(4);

                busy_wait_us_32(800000);

                // Expected
                flash_code(message);

                busy_wait_us_32(800000);

                // Actual
                flash_code(q_item.message);

                busy_wait_us_32(2000000);

                // Remove the message and exit loop
                queue_remove_blocking(&interprocess_queue, &q_item);
                return q_item.message;
            }
        }
    }
}

uint8_t intercore_queue_peek_message()
{
    interprocess_queue_message_t q_item;

    if (!queue_try_peek(&interprocess_queue, &q_item))
    {
        return Q_MT_NONE;
    }

    return q_item.message;
}

void intercore_queue_add_and_wait_message(uint8_t send_message, uint8_t wait_message)
{
    intercore_queue_add_message(send_message);
    intercore_queue_wait_message(wait_message);
}

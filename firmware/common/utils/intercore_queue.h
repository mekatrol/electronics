#ifndef __INTERCORE_QUEUE_H__
#define __INTERCORE_QUEUE_H__

#include "pico/stdlib.h"

#define Q_MT_NONE 0x00        // No message
#define Q_MT_PAUSE_IRQ 0x01   // Request to pause
#define Q_MT_RESTORE_IRQ 0x02 // Request to restore
#define Q_MT_PAUSED_IRQ 0x03  // IRQ paused

void intercore_queue_init();
uint8_t intercore_queue_block_message();
void intercore_queue_add_message(uint8_t message);
bool intercore_queue_try_add_message(uint8_t message);
uint8_t intercore_queue_wait_message(uint8_t message);
uint8_t intercore_queue_peek_message();
void intercore_queue_add_and_wait_message(uint8_t send_message, uint8_t wait_message);

#endif // __INTERCORE_QUEUE_H__
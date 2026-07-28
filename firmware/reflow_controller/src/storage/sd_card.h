#ifndef REFLOW_SD_CARD_H
#define REFLOW_SD_CARD_H

#include <stdbool.h>
#include <stdint.h>

typedef enum
{
  SD_CARD_UNINITIALIZED,
  SD_CARD_INITIALIZING,
  SD_CARD_READY,
  SD_CARD_ERROR
} sd_card_state_t;

void sd_card_initialize(void);
void sd_card_service(void);
sd_card_state_t sd_card_state(void);
bool sd_card_read_block(uint32_t block, uint8_t *destination);

#endif

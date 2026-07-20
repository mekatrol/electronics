#ifndef __CONTROLLER_INIT_H__
#define __CONTROLLER_INIT_H__

#include "pico/stdlib.h"

bool controller_init_startup();
bool controller_init_reset_flash(uint16_t page_addr, uint8_t *page_buf);
bool controller_flash_is_initialised(uint8_t *page_buf);

#endif // __CONTROLLER_INIT_H__
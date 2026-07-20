#ifndef __TTY_H__
#define __TTY_H__

#include "pico/stdlib.h"

#ifndef TTY_BUFFER_SIZE
#define TTY_BUFFER_SIZE 1024
#endif // TTY_BUFFER_SIZE

uint16_t tty_tick(char *line);
void tty_prompt();

#endif // __TTY_H__
#ifndef __IO_H__
#define __IO_H__

#include "pico/stdlib.h"

inline void set_io(uint pin, bool value, bool inverted)
{
  if (inverted)
  {
    value = !value;
  }

  gpio_put(pin, value);
}

#endif // __IO_H__
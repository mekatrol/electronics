#ifndef __I2C_UTIL_H__
#define __I2C_UTIL_H__

#include "pico/stdlib.h"

int i2c_reg_write(i2c_inst_t *i2c,
                  const uint addr,
                  const uint8_t reg,
                  uint8_t *buf,
                  const uint8_t nbytes);

int i2c_reg_read(i2c_inst_t *i2c,
                 const uint addr,
                 const uint8_t reg,
                 uint8_t *buf,
                 const uint8_t nbytes);

#endif // __I2C_UTIL_H__
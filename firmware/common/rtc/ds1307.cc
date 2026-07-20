#include <stdio.h>
#include "pico/stdlib.h"

#include "DS1307.h"
#include "../utils/bcd.h"
#include "../utils/i2c_util.h"

static const uint8_t DS1307_ADDR = 0x68;

DS1307::DS1307(
    i2c_inst_t *i2c,
    uint cs_pin,
    uint clk_pin,
    uint dat_pin)
{
  this->i2c = i2c;
  this->cs_pin = cs_pin;
  this->clk_pin = clk_pin;
  this->dat_pin = dat_pin;

  // Initialize I2C port at 80 kHz
  i2c_init(i2c, 80 * 1000);

  // Initialize I2C pins
  gpio_set_function(dat_pin, GPIO_FUNC_I2C);
  gpio_set_function(clk_pin, GPIO_FUNC_I2C);
}

DS1307::~DS1307()
{
}

void DS1307::Init(datetime_t *dt, uint8_t control)
{
  uint8_t data[8] = {
      bin2bcd(dt->sec),
      bin2bcd(dt->min),
      bin2bcd(dt->hour),
      (uint8_t)dt->dotw,
      bin2bcd(dt->day),
      bin2bcd(dt->month),
      bin2bcd(dt->year - 2000U), // Assume 2 digit year 00 is 4 digit year 2000
      control};

  i2c_reg_write(this->i2c, DS1307_ADDR, 0, data, 8);
}

void DS1307::GetRam(uint8_t *buffer, uint8_t offset, uint8_t len)
{
  // Read from device at specified offset with specified length
  i2c_reg_read(this->i2c, DS1307_ADDR, offset, buffer, len);
}

void DS1307::SetRam(uint8_t *buffer, uint8_t offset, uint8_t len)
{
  // Write to device at specified offset with specified length
  i2c_reg_write(this->i2c, DS1307_ADDR, offset, buffer, len);
}

void DS1307::SetRamDateTime(uint8_t *buffer, datetime_t *dt)
{
  buffer[0] = bin2bcd(dt->sec);
  buffer[1] = bin2bcd(dt->min);
  buffer[2] = bin2bcd(dt->hour);
  buffer[3] = (uint8_t)dt->dotw;
  buffer[4] = bin2bcd(dt->day);
  buffer[5] = bin2bcd(dt->month);
  buffer[6] = bin2bcd(dt->year - 2000U); // Assume 2 digit year 00 is 4 digit year 2000
  buffer[7] = 0;                         // SQWE
}

void DS1307::SetDateTime(datetime_t *dt)
{
  uint8_t data[8];

  SetRamDateTime(data, dt);

  i2c_reg_write(this->i2c, DS1307_ADDR, 0, data, 7); // Ignore SQWE
}

void DS1307::GetDateTime(datetime_t *dt)
{
  uint8_t data[7];

  // Read device ID to make sure that we can communicate with the ADXL343
  i2c_reg_read(this->i2c, DS1307_ADDR, 0, data, 7);

  if (dt)
  {
    dt->year = bcd2bin(data[6]) + 2000U;
    dt->month = bcd2bin(data[5]);
    dt->day = bcd2bin(data[4]);
    dt->hour = bcd2bin(data[2]);
    dt->min = bcd2bin(data[1]);
    dt->sec = bcd2bin(data[0] & 0x7F);
    dt->dotw = data[3];
  }
}
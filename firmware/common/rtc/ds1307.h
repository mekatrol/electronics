#ifndef __DS1307_H__
#define __DS1307_H__

#include "pico/stdlib.h"
#include "hardware/i2c.h"

#define RTC_INIT_SIGNATURE 0xA596

class DS1307
{
public:
  DS1307(i2c_inst_t *i2c, uint cs_pin, uint clk_pin, uint dat_pin);
  ~DS1307();

  void Init(datetime_t *dt, uint8_t control);

  void GetRam(uint8_t *buffer, uint8_t offset, uint8_t len);
  void SetRam(uint8_t *buffer, uint8_t offset, uint8_t len);
  void SetRamDateTime(uint8_t *buffer, datetime_t *dt);

  void SetDateTime(datetime_t *dt);
  void GetDateTime(datetime_t *dt);

private:
  i2c_inst_t *i2c;
  uint cs_pin;
  uint clk_pin;
  uint dat_pin;
};

#endif // __DS1307_H__
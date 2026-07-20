#ifndef __CONFIG_H__
#define __CONFIG_H__

#define EEPROM_INITIALISED 0xA5

typedef struct config
{
    uint8_t initisalised;
    uint8_t preheat_setpoint;
    uint8_t soak_setpoint;
    uint8_t reflow_setpoint;
    uint8_t cool_setpoint;
    uint8_t overshoot_delta;
} config_t;

extern config_t config;

void config_init();
void config_dump();

#endif // __CONFIG_H__
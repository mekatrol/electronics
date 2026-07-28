#include <Arduino.h>
#include <EEPROM.h>

#include "config.h"
#include "stage.h"

static config_t config;

void config_init()
{
    uint8_t config_size = sizeof(config_t);

    uint8_t i = 0;
    if (EEPROM.read(0) == EEPROM_INITIALISED)
    {
        uint8_t *p = (uint8_t *)&config;
        for (i = 0; i < config_size; i++)
        {
            p[i] = EEPROM.read(i);
        }

        return;
    }

    config.initisalised = EEPROM_INITIALISED;
    config.preheat_setpoint = STG_PREHEAT_SETPOINT;
    config.soak_setpoint = STG_SOAK_SETPOINT;
    config.reflow_setpoint = STG_REFLOW_SETPOINT;
    config.cool_setpoint = STG_COOL_SETPOINT;
    config.overshoot_delta = STG_OVERSHOOT_DELTA;

    uint8_t *p = (uint8_t *)&config;
    for (i = 0; i < config_size; i++)
    {
        EEPROM.write(i, *(p + i));
    }
}

void config_dump()
{
    Serial.println("EEPROM config settings:");
    Serial.print("  initialised:      ");
    Serial.println(config.initisalised);
    Serial.print("  preheat_setpoint: ");
    Serial.println(config.preheat_setpoint);
    Serial.print("  soak_setpoint:    ");
    Serial.println(config.soak_setpoint);
    Serial.print("  reflow_setpoint:  ");
    Serial.println(config.reflow_setpoint);
    Serial.print("  cool_setpoint:    ");
    Serial.println(config.cool_setpoint);
    Serial.print("  overshoot_delta:  ");
    Serial.println(config.overshoot_delta);
}

#include "pins.h"
#include "average.h"
#include "config.h"
#include "lcd.h"
#include "learn.h"
#include "reflow.h"
#include "stage.h"
#include "temperature.h"
#include "temp_sensor.h"
#include "ui.h"

uint32_t tick_avg_sensor = 0;
uint32_t tick_pid = 0;

void plot_trend(float value, float t1, float t2, uint8_t stage);

void setup()
{
    pinMode(HEAT_PIN, OUTPUT);
    digitalWrite(HEAT_PIN, LOW);

    pinMode(FAN_PIN, OUTPUT);
    digitalWrite(FAN_PIN, LOW);

    ui_init();

    Serial.begin(9600);

    config_init();

    // Write out config settings
    config_dump();
}

void loop()
{
    uint32_t this_tick = millis();
    uint32_t delta_tick = this_tick - tick_avg_sensor;

    // Check change stage
    if (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
    {
        digitalWrite(BEEPER_PIN, HIGH);
        while (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
        {
            ;
        }
        digitalWrite(BEEPER_PIN, LOW);

        reflow_run();
    }

    // More than 200ms elapsed?
    if (delta_tick < 200)
    {
        // Do nothing this loop
        delay(10);
        return;
    }
    tick_avg_sensor = this_tick;

    tick_pid++;
    if (tick_pid >= 5)
    {
        tick_pid = 0;
        ui_update(read_sensor_1(), read_sensor_2(), read_sensor_average(), 0, 0, NULL);
    }

    if (read_sensor_average() < 25)
    {
        digitalWrite(FAN_PIN, LOW);
    }
}

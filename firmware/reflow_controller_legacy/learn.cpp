#include <Arduino.h>

#include "config.h"
#include "lcd.h"
#include "learn.h"
#include "pins.h"
#include "stage.h"
#include "temp_sensor.h"
#include "ui.h"

uint32_t learn_next_process_tick = 0;
char learn_ui_buffer[LINE_BUFFER_SIZE];

float get_secs(uint32_t ms_start, uint32_t ms_end)
{
    return ((float)ms_end - (float)ms_start) / 1000.0f;
}

float rate_of_change(float temp_start, float temp_end, uint32_t ms_start, uint32_t ms_end)
{
    float dt_temp = temp_end - temp_start;
    float dt_secs = get_secs(ms_start, ms_end);

    return dt_temp / dt_secs;
}

void learn_send_warm_result(uint8_t stage, float temp_start, float temp_end, uint32_t ms_start, uint32_t ms_end)
{
    Serial.print(stage_get_stage_name(stage));

    Serial.print(" started at ");
    ui_append_float(learn_ui_buffer, temp_start, true);
    Serial.print(learn_ui_buffer);
    Serial.print("C ");

    Serial.print("finished at ");
    ui_append_float(learn_ui_buffer, temp_end, true);
    Serial.print(learn_ui_buffer);
    Serial.print("C ");

    Serial.print("and took ");
    ui_append_float(learn_ui_buffer, get_secs(ms_start, ms_end), true);
    Serial.print(learn_ui_buffer);

    Serial.print("s with a rate of change of ");
    float roc = rate_of_change(temp_start, read_sensor_average(), ms_start, ms_end);
    ui_append_float(learn_ui_buffer, roc, true);
    Serial.print(learn_ui_buffer);
    Serial.println("C/s");
}

bool learn_stage(uint8_t stage, float setpoint)
{
    uint32_t tick = millis();
    uint32_t tick_start = tick;

    stage_set_current_stage(stage);

    float temp_start = read_sensor_average();

    while (read_sensor_average() < setpoint)
    {
        tick = millis();
        if (tick > learn_next_process_tick)
        {
            learn_next_process_tick = tick + 500;
            ui_update(read_sensor_1(), read_sensor_2(), read_sensor_average(), setpoint, 0, NULL);
        }

        if (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
        {
            digitalWrite(HEAT_PIN, LOW);
            return false;
        }
    }

    tick = millis();

    learn_send_warm_result(stage, temp_start, read_sensor_average(), tick_start, tick);

    return true;
}

void learn_send_overshoot_result(float temp_start, float temp_end, uint32_t ms_start, uint32_t ms_end)
{
    Serial.print(stage_get_stage_name(stage_get_current_stage()));

    Serial.print(" started at ");
    ui_append_float(learn_ui_buffer, temp_start, true);
    Serial.print(learn_ui_buffer);
    Serial.print("C ");

    Serial.print("peaked at ");
    ui_append_float(learn_ui_buffer, temp_end, true);
    Serial.print(learn_ui_buffer);
    Serial.print("C ");

    Serial.print("and took ");
    ui_append_float(learn_ui_buffer, get_secs(ms_start, ms_end), true);
    Serial.print(learn_ui_buffer);

    Serial.print("s with a rate of change of ");
    float roc = rate_of_change(temp_start, read_sensor_average(), ms_start, ms_end);
    ui_append_float(learn_ui_buffer, roc, true);
    Serial.print(learn_ui_buffer);
    Serial.println("C/s");
}

bool learn_overshoot(uint8_t stage, float setpoint)
{
    float prev_temp = read_sensor_average();
    uint32_t tick = millis();
    uint32_t tick_start = tick;

    stage_set_current_stage(stage);

    // Init temperatures
    float temp_start = setpoint;
    float next_temp;

    // Temperature rise has peaked count
    int temp_peaked_count = 0;

    // While we have not peaked
    while (temp_peaked_count <= 5)
    {
        tick = millis();

        // Time to update state?
        if (tick > learn_next_process_tick)
        {
            // Get average temp
            next_temp = read_sensor_average();

            // Have we peaked?
            if (next_temp <= prev_temp)
            {
                // Increment peak count
                temp_peaked_count++;
            }
            else
            {
                // Decrement peak count
                if (temp_peaked_count > 0)
                {
                    temp_peaked_count--;
                }
            }

            // Remember this
            prev_temp = next_temp;

            learn_next_process_tick = tick + 200;
            ui_update(read_sensor_1(), read_sensor_2(), read_sensor_average(), setpoint, 0, NULL);
        }

        if (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
        {
            digitalWrite(HEAT_PIN, LOW);
            return false;
        }
    }

    tick = millis();

    learn_send_overshoot_result(temp_start, prev_temp, tick_start, tick);

    return true;
}

void learn_finished()
{
    digitalWrite(HEAT_PIN, LOW);
    digitalWrite(FAN_PIN, HIGH);
}

void learn_run()
{
    // Turn off fan
    digitalWrite(FAN_PIN, LOW);

    // Start heat
    digitalWrite(HEAT_PIN, HIGH);

    // Warm to preheat temperature, this ensures that the elements
    // have warmed up and the learn time does not include element warm up
    if (!learn_stage(STG_PREHEAT, config.preheat_setpoint))
    {
        learn_finished();
        return;
    }

    // Warm to soak temperature, this ensures that the board
    // warms evenly
    if (!learn_stage(STG_SOAK, config.soak_setpoint))
    {
        learn_finished();
        return;
    }

    // Warm to reflow temperature
    if (!learn_stage(STG_REFLOW, config.reflow_setpoint))
    {
        learn_finished();
        return;
    }

    // Stop heat
    digitalWrite(HEAT_PIN, LOW);

    if (!learn_overshoot(STG_TEST_OVERSHOOT, config.reflow_setpoint))
    {
        learn_finished();
        return;
    }

    learn_finished();
}

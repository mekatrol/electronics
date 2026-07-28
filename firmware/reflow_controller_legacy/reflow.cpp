#include <Arduino.h>

#include "lcd.h"
#include "config.h"
#include "pins.h"
#include "reflow.h"
#include "stage.h"
#include "temp_sensor.h"
#include "ui.h"

#define RUN_TICK_MAX_VAL 4294967295
#define RUN_TICK_TOGGLE_PERIOD 5000
#define RUN_TICK_4_MINS 240000
#define RUN_TICK_DWELL 60000

uint32_t run_next_process_tick = 0;
uint32_t run_cycle_toggle_tick = 0;
uint8_t run_cycle_is_on = 0;
uint8_t run_cycle_flag = 0;

char run_ui_buffer[LINE_BUFFER_SIZE];

void run_heat_cycle(uint32_t tick, float temp, float setpoint)
{
    if (tick > run_cycle_toggle_tick)
    {
        run_cycle_is_on = !run_cycle_is_on;
        run_cycle_toggle_tick = tick + RUN_TICK_TOGGLE_PERIOD;
    }

    if (run_cycle_is_on && temp < setpoint)
    {
        digitalWrite(HEAT_PIN, HIGH);
    }
    else
    {
        digitalWrite(HEAT_PIN, LOW);
    }
}

void run_init_cycle(uint32_t tick)
{
    run_cycle_is_on = 1;
    run_cycle_toggle_tick = RUN_TICK_MAX_VAL;
    run_cycle_flag = 0;
}

bool reflow_stage(uint8_t stage, float setpoint, uint32_t end_dwell)
{
    uint32_t tick = millis();

    stage_set_current_stage(stage);
    run_init_cycle(tick);

    float temp_start = read_sensor_average();
    float temp;

    while ((temp = read_sensor_average()) < setpoint)
    {
        tick = millis();

        // Switch to heat cycle mode?
        if (temp > (setpoint - config.overshoot_delta) && run_cycle_toggle_tick == RUN_TICK_MAX_VAL)
        {
            run_cycle_toggle_tick = tick + RUN_TICK_TOGGLE_PERIOD;
            run_cycle_flag = UI_FLAG_CYCLE;
        }

        run_heat_cycle(tick, temp, setpoint);

        if (tick > run_next_process_tick)
        {
            run_next_process_tick = tick + 500;
            ui_update(read_sensor_1(), read_sensor_2(), read_sensor_average(), setpoint, run_cycle_flag, NULL);
        }

        if (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
        {
            digitalWrite(HEAT_PIN, LOW);
            while (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
            {
                ;
            }
            return false;
        }
    }

    tick = millis();
    run_next_process_tick = tick;
    uint32_t tick_end = tick + end_dwell;

    ui_update(read_sensor_1(), read_sensor_2(), read_sensor_average(), setpoint, UI_FLAG_DWELL | run_cycle_flag, RUN_TICK_DWELL / 1000);

    while (tick < tick_end)
    {
        temp = read_sensor_average();
        run_heat_cycle(tick, temp, setpoint);

        uint32_t delta = tick_end - tick;
        uint8_t remaining = delta / 1000;

        if (tick > run_next_process_tick)
        {
            run_next_process_tick = tick + 500;
            ui_update(read_sensor_1(), read_sensor_2(), read_sensor_average(), setpoint, UI_FLAG_DWELL | run_cycle_flag, &remaining);
        }

        if (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
        {
            digitalWrite(HEAT_PIN, LOW);
            while (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
            {
                ;
            }
            return false;
        }

        tick = millis();
    }

    return true;
}

void reflow_finished()
{
    digitalWrite(HEAT_PIN, LOW);
    digitalWrite(FAN_PIN, HIGH);
    stage_set_current_stage(STG_IDLE);
}

void reflow_run()
{
    // Turn off fan
    digitalWrite(FAN_PIN, LOW);

    // Start heat
    digitalWrite(HEAT_PIN, HIGH);

    // Warm to preheat temperature, this ensures that the elements
    // have warmed up and the learn time does not include element warm up
    if (!reflow_stage(STG_PREHEAT, config.preheat_setpoint, RUN_TICK_DWELL))
    {
        reflow_finished();
        return;
    }

    // Warm to soak temperature, this ensures that the board
    // warms evenly
    if (!reflow_stage(STG_SOAK, config.soak_setpoint, RUN_TICK_DWELL))
    {
        reflow_finished();
        return;
    }

    // Warm to reflow temperature
    if (!reflow_stage(STG_REFLOW, config.reflow_setpoint, RUN_TICK_DWELL))
    {
        reflow_finished();
        return;
    }

    // Stop heat
    reflow_finished();
}
#include "average.h"
#include "pins.h"
#include "temperature.h"

average_set_t avg_sensor_1;
average_set_t avg_sensor_2;

float read_sensor_1()
{
    uint16_t temp_raw = average_calc(&avg_sensor_1, analogRead(T1_PIN));
    return temp_analog_to_celsius(temp_raw);
}

float read_sensor_2()
{
    uint16_t temp_raw = average_calc(&avg_sensor_2, analogRead(T2_PIN));
    return temp_analog_to_celsius(temp_raw);
}

float read_sensor_average()
{
    return (read_sensor_1() + read_sensor_2()) / 2.0f;
}
#ifndef __PID_H__
#define __PID_H__

#include <Arduino.h>

typedef struct pid_data
{
    // Interval running values
    float output;
    float error;
    float error_sum;
    uint32_t last_tick;

    // Set to true once initialised
    bool initialised;

    // PID values
    float Kp;
    float Ki;
    float Kd;
    float divisor;
    float setpoint;

    // Limit output values
    float limit_min;
    float limit_max;
    bool limit_enabled;
} pid_data_t;

void pid_init(pid_data_t *pid_data, float setpoint, uint32_t start_tick);
void pid_adjust_parameters(pid_data_t *pid_data, float Kp, float Ki, float Kd);
void pid_set_limits(pid_data_t *pid_data, float min, float max);
float pid_compute(pid_data_t *pid_data, float input, uint32_t this_tick);

#endif // __PID_H__
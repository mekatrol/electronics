#include "pid.h"

void pid_init(pid_data_t *pid_data, float setpoint, uint32_t start_tick)
{
    pid_data->setpoint = setpoint;
    pid_data->Kp = 2;
    pid_data->Ki = 1;
    pid_data->Kd = 1;
    pid_data->divisor = 10;

    pid_data->limit_enabled = 0;

    // Interval values
    pid_data->error = 0;
    pid_data->error_sum = 0;
    pid_data->last_tick = start_tick;

    // Struct is now initialised
    pid_data->initialised = 1;
}

void pid_adjust_parameters(pid_data_t *pid_data, float Kp, float Ki, float Kd)
{
    // All must be greater than zero to be valid (else math breaks)
    if (Kp < 0 || Ki < 0 || Kd < 0)
    {
        return;
    }

    pid_data->Kp = Kp;
    pid_data->Ki = Ki;
    pid_data->Kd = Kd;
}

void pid_set_limits(pid_data_t *pid_data, float min, float max)
{
    pid_data->limit_min = min;
    pid_data->limit_max = max;
    pid_data->limit_enabled = 1;
}

float pid_compute(pid_data_t *pid_data, float input, uint32_t this_tick)
{
    // Must be initialised to run
    if (!pid_data->initialised)
    {
        return 0;
    }

    // Calculate time difference since last time executed
    float time_delta = (float)(this_tick - pid_data->last_tick);

    // Calculate error P I D
    float error = pid_data->setpoint - input;

    pid_data->error += error * time_delta;

    if (pid_data->limit_enabled)
    {
        pid_data->error_sum = constrain(pid_data->error_sum, pid_data->limit_min * 1.01, pid_data->limit_max * 1.01);
    }

    float error_delta = (error - pid_data->error) / time_delta;

    // Calculate the new output
    float calculated = (pid_data->Kp * error + pid_data->Ki * pid_data->error_sum + pid_data->Kd * error_delta) / pid_data->divisor;

    // If limit is specified, limit the output
    if (pid_data->limit_enabled)
    {
        pid_data->output = constrain(calculated, pid_data->limit_min, pid_data->limit_max);
    }
    else
    {
        pid_data->output = calculated;
    }

    // Keep track of interval values
    pid_data->error = error;
    pid_data->last_tick = this_tick;

    // Return the computed output
    return pid_data->output;
}
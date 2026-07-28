#include "plot.h"
#include "stage.h"

void plot_trend(float setpoint, float t1, float t2, float avg)
{
    Serial.print(setpoint);
    Serial.print(",");
    Serial.print(t1);
    Serial.print(",");
    Serial.print(t2);
    Serial.print(",");
    Serial.println(avg);
}
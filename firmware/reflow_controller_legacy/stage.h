#ifndef __STAGE_H__
#define __STAGE_H__

#include <Arduino.h>

// No reflow active
#define STG_IDLE 0
#define STG_IDLE_NAME "IDLE"

// Bring the heat plate from ambient up to pre-heat setpoint
// about 2°C to 3°C per second, eg setpoint is often 125°C
#define STG_PREHEAT 1
#define STG_PREHEAT_NAME "PREHEAT"
#define STG_PREHEAT_SETPOINT 125

// Bring the heat plate up to eutectic transformation setpoint
// about 0.5°C to 1°C per second, eg setpoint is often 185°C
#define STG_SOAK 2
#define STG_SOAK_NAME "SOAK"
#define STG_SOAK_SETPOINT 160

// Solder now liquid, rapid rise to 230°C from pre-flow setpoint
// Reflow should last about 30 seconds
#define STG_REFLOW 3
#define STG_REFLOW_NAME "REFLOW"
#define STG_REFLOW_SETPOINT 195

// Cool to ambient, the rate shpuld be about 3°C per second.
// Do not exceed 5°C else dry joint may occur
#define STG_COOL 4
#define STG_COOL_NAME "COOL"
#define STG_COOL_SETPOINT 0

// Testing temperature overshoot
#define STG_TEST_OVERSHOOT 5
#define STG_TEST_OVERSHOOT_NAME "OVERSHOOT"
#define STG_OVERSHOOT_DELTA 25

uint8_t stage_get_current_stage();
uint8_t stage_set_current_stage(uint8_t stage);
const char *stage_get_stage_name(uint8_t stage);

#endif // __STAGE_H__
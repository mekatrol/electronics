#include "stage.h"

uint8_t stage_current = STG_IDLE;

uint8_t stage_get_current_stage()
{
    return stage_current;
}

uint8_t stage_set_current_stage(uint8_t stage)
{
    switch (stage)
    {
    case STG_IDLE:
    case STG_PREHEAT:
    case STG_SOAK:
    case STG_REFLOW:
    case STG_COOL:
    case STG_TEST_OVERSHOOT:
        stage_current = stage;
        return stage_current;

    default:
        return stage_current;
    }
}

const char *stage_get_stage_name(uint8_t stage)
{
    switch (stage)
    {
    case STG_IDLE:
        return STG_IDLE_NAME;

    case STG_PREHEAT:
        return STG_PREHEAT_NAME;

    case STG_SOAK:
        return STG_SOAK_NAME;

    case STG_REFLOW:
        return STG_REFLOW_NAME;

    case STG_COOL:
        return STG_COOL_NAME;

    case STG_TEST_OVERSHOOT:
        return STG_TEST_OVERSHOOT_NAME;

    default:
        return "UNK";
    }
}

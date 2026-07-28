#include "average.h"

uint16_t average_calc(average_set_t *set, uint16_t value)
{
    if (!set->initialised)
    {
        set->v1 = value;
        set->v2 = value;
        set->v3 = value;
        set->v4 = value;
        set->v5 = value;
        set->initialised = true;

        return value;
    }

    set->v5 = set->v4;
    set->v4 = set->v3;
    set->v3 = set->v2;
    set->v2 = set->v1;
    set->v1 = value;

    return (set->v5 + set->v4 + set->v3 + set->v2 + set->v1) / 5;
}
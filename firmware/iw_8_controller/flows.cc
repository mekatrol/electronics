#include <stdio.h>

#include "flows.h"

uint8_t *flow_digital_registers = nullptr;
float *flow_analogue_registers = nullptr;
datetime_t *flow_date_time_registers = nullptr;
flow_function_t *flow_functions;

size_t flows_get_function_type_size(uint16_t flow_function_type)
{
  switch (flow_function_type)
  {
  case FLOW_TYPE_AVG:
    return sizeof(flow_function_t);
  case FLOW_TYPE_AND:
    return sizeof(flow_function_t);
  case FLOW_TYPE_OR:
    return sizeof(flow_function_t);
  case FLOW_TYPE_NAND:
    return sizeof(flow_function_t);
  case FLOW_TYPE_NOR:
    return sizeof(flow_function_t);
  case FLOW_TYPE_INVERT:
    return sizeof(flow_function_t);
  case FLOW_TYPE_XOR:
    return sizeof(flow_function_t);
  case FLOW_TYPE_XNOR:
    return sizeof(flow_function_t);
  case FLOW_TYPE_COMPARE:
    return sizeof(flow_function_t);
  case FLOW_TYPE_PID:
    return sizeof(flow_function_t);
  case FLOW_TYPE_DELAY:
    return sizeof(flow_function_t);
  case FLOW_TYPE_PULSE:
    return sizeof(flow_function_t);
  case FLOW_TYPE_RANGE:
    return sizeof(flow_function_t);
  case FLOW_TYPE_LOOP:
    return sizeof(flow_function_t);
  case FLOW_TYPE_IF:
    return sizeof(flow_function_t);
  case FLOW_TYPE_MIN:
    return sizeof(flow_function_t);
  case FLOW_TYPE_MAX:
    return sizeof(flow_function_t);
  case FLOW_TYPE_SEQ:
    return sizeof(flow_function_t);
  case FLOW_TYPE_TIME_SCHED:
    return sizeof(flow_function_t);

  default:
    return sizeof(flow_function_t);
  }
}

const char *flows_get_function_name(uint16_t flow_function_type)
{
  switch (flow_function_type)
  {
  case FLOW_TYPE_AVG:
    return FLOW_TYPE_AVG_STR;
  case FLOW_TYPE_AND:
    return FLOW_TYPE_AND_STR;
  case FLOW_TYPE_OR:
    return FLOW_TYPE_OR_STR;
  case FLOW_TYPE_NAND:
    return FLOW_TYPE_NAND_STR;
  case FLOW_TYPE_NOR:
    return FLOW_TYPE_NOR_STR;
  case FLOW_TYPE_INVERT:
    return FLOW_TYPE_INVERT_STR;
  case FLOW_TYPE_XOR:
    return FLOW_TYPE_XOR_STR;
  case FLOW_TYPE_XNOR:
    return FLOW_TYPE_XNOR_STR;
  case FLOW_TYPE_COMPARE:
    return FLOW_TYPE_COMPARE_STR;
  case FLOW_TYPE_PID:
    return FLOW_TYPE_PID_STR;
  case FLOW_TYPE_DELAY:
    return FLOW_TYPE_DELAY_STR;
  case FLOW_TYPE_PULSE:
    return FLOW_TYPE_PULSE_STR;
  case FLOW_TYPE_RANGE:
    return FLOW_TYPE_RANGE_STR;
  case FLOW_TYPE_LOOP:
    return FLOW_TYPE_LOOP_STR;
  case FLOW_TYPE_IF:
    return FLOW_TYPE_IF_STR;
  case FLOW_TYPE_MIN:
    return FLOW_TYPE_MIN_STR;
  case FLOW_TYPE_MAX:
    return FLOW_TYPE_MAX_STR;
  case FLOW_TYPE_SEQ:
    return FLOW_TYPE_SEQ_STR;
  case FLOW_TYPE_TIME_SCHED:
    return FLOW_TYPE_TIME_SCHED_STR;
  default:
    return "UNK";
  }
}

void flows_dump_list()
{
  printf("\r\n<flows start>\r\n");

  if (flow_functions == nullptr)
  {
    printf("There are no flows.\r\n");
  }
  else
  {
    flow_function_t *f = flow_functions;

    while (f != nullptr)
    {
      const char *name = flows_get_function_name(f->type);
      printf("'%s'\r\n", name);

      f = f->next;
    }
  }

  printf("<flows end>\r\n");
}

#ifndef __REGISTERS_H__
#define __REGISTERS_H__

#include "pico/stdlib.h"

#include "../common/utils/linked_list.h"

#define FLOW_DIGITAL_REGISTER_COUNT 1000
#define FLOW_ANALOG_REGISTER_COUNT 1000
#define FLOW_DATETIME_REGISTER_COUNT 100

#define FLOW_IO_ENABLED_BIT 0x80
#define FLOW_IO_DIRECTION_BIT 0x40

#define FLOW_FUNCTION_MAX_IO 20
#define FLOW_FUNCTION_COUNT 200
#define FLOW_FUNCTION_ENABLED_BIT 0x8000

#define FLOW_TYPE_AVG 1         // Average two values
#define FLOW_TYPE_AND 2         // AND two values
#define FLOW_TYPE_OR 3          // OR two values
#define FLOW_TYPE_NAND 4        // NAND two values
#define FLOW_TYPE_NOR 5         // NOR two values
#define FLOW_TYPE_INVERT 6      // Invert a single value
#define FLOW_TYPE_XOR 7         // XOR two values
#define FLOW_TYPE_XNOR 8        // XNOR two values
#define FLOW_TYPE_COMPARE 9     // Compare two values
#define FLOW_TYPE_PID 10        // PID controller
#define FLOW_TYPE_DELAY 11      // Delay change in value (digital)
#define FLOW_TYPE_PULSE 12      // Trigger pulse (digital)
#define FLOW_TYPE_RANGE 13      // Convert analogue range to analogu range
#define FLOW_TYPE_LOOP 14       // Loop a series of functions n times
#define FLOW_TYPE_IF 15         // Logic if
#define FLOW_TYPE_MIN 16        // Minimum of two analogue values
#define FLOW_TYPE_MAX 17        // Maximum of two analogue values
#define FLOW_TYPE_SEQ 18        // Sequence 1 to 8 outputs based on an input condition
#define FLOW_TYPE_TIME_SCHED 19 // Time scheduling (current date time equals, within, etc)

#define FLOW_TYPE_AVG_STR "AVG"         // Average two values
#define FLOW_TYPE_AND_STR "AND"         // AND two values
#define FLOW_TYPE_OR_STR "OR"           // OR two values
#define FLOW_TYPE_NAND_STR "NAND"       // NAND two values
#define FLOW_TYPE_NOR_STR "NOR"         // NOR two values
#define FLOW_TYPE_INVERT_STR "INV"      // Invert a single value
#define FLOW_TYPE_XOR_STR "XOR"         // XOR two values
#define FLOW_TYPE_XNOR_STR "XNOR"       // XNOR two values
#define FLOW_TYPE_COMPARE_STR "CMP"     // Compare two values
#define FLOW_TYPE_PID_STR "PID"         // PID controller
#define FLOW_TYPE_DELAY_STR "DLY"       // Delay change in value (digital)
#define FLOW_TYPE_PULSE_STR "PLS"       // Trigger pulse (digital)
#define FLOW_TYPE_RANGE_STR "RNG"       // Convert analogue range to analogu range
#define FLOW_TYPE_LOOP_STR "LOOP"       // Loop a series of functions n times
#define FLOW_TYPE_IF_STR "IF"           // Logic if
#define FLOW_TYPE_MIN_STR "MIN"         // Minimum of two analogue values
#define FLOW_TYPE_MAX_STR "MAX"         // Maximum of two analogue values
#define FLOW_TYPE_SEQ_STR "SEQ"         // Sequence 1 to 8 outputs based on an input condition
#define FLOW_TYPE_TIME_SCHED_STR "SCHD" // Time scheduling (current date time equals, within, etc)

typedef struct flow_function
{
  /// @brief The next flow in the sequence, or nullptr if not more flows
  flow_function *next;

  /// @brief The flow type
  uint16_t type;

  /// @brief The flow flags, eg enabled
  uint16_t flags;

  /// @brief The data associated with this flow, data size and value
  ///        will depend on the flow type.
  void *data;
} flow_function_t;

extern uint8_t *flow_digital_registers;

extern float *flow_analogue_registers;

extern datetime_t *flow_date_time_registers;

extern flow_function_t *flow_functions;

void flows_dump_list();

size_t flows_get_function_type_size(uint16_t flow_function_type);

const char *flows_get_function_name(uint16_t flow_function_type);

#endif // __REGISTERS_H__
#ifndef __STATE_H__
#define __STATE_H__

#include <string.h>

#include "pico/stdlib.h"

#include "../common/communication/serial.h"

static const char FLASH_INIT_MARKER_MAXLEN = 16;
static const char *FLASH_INIT_MARKER = "IW_IW_8\0";
static const int FLASH_INIT_MARKER_LEN = strlen(FLASH_INIT_MARKER) + 1; // + 1 to include null terminator embedded in string
static const int FLASH_VERSION[] = {0, 1, 0, 0};
static const int CONTROLLER_VERSION[] = {0, 1, 0, 0};

#define RUN_STATE_FLASH_AVAILABLE 0x01

/********************************************************************
 * I/O state definition
 ********************************************************************/
typedef struct controller_io_state
{
  uint32_t overridden;
  uint32_t override_value;
  uint32_t state;
} controller_io_state_t;

/********************************************************************
 * Run state definition
 ********************************************************************/
typedef struct run_state
{
  uint8_t version[4];            // Four bytes for controller version x.x.x.x, eg: 1.0.0.0
  uint8_t flags;                 // Bit flags for run state
  uint16_t flash_id;             // The unique id of the flash device
  datetime_t date_time;          // Current date & time
  controller_io_state_t inputs;  // Bits for digital inputs, includes ADC inputs on/off state
  controller_io_state_t outputs; // Bits for 595 digital outputs
  uint16_t adc0;                 // ADC 0 value
  uint16_t adc1;                 // ADC 1 value
  uint16_t adc2;                 // ADC 2 value
} run_state_t;

/********************************************************************
 * Flash configuration definition
 ********************************************************************/
typedef struct flash_config
{
  char marker[FLASH_INIT_MARKER_MAXLEN]; // The current flash marker
  uint8_t version[4];                    // Four bytes for flash data version x.x.x.x, eg: 1.0.0.0
} flash_config_t;

/********************************************************************
 * Configuration definition
 ********************************************************************/
typedef struct controller_config
{
  flash_config_t flash;
  serial_conf_t uart_0;
  serial_conf_t uart_1;
} controller_config_t;

/********************************************************************
 * Global structs
 ********************************************************************/
extern controller_config_t controller_config;
extern run_state_t run_state;

#endif // __STATE_H__
#ifndef __PROTOCOL_H__
#define __PROTOCOL_H__

#include "pico/stdlib.h"

#define GLOBAL_ADDR 0xFFFF

#define MSG_SOM '<'
#define MSG_EOM '>'

#define MT_NONE 0x0000            // No message type value
#define MT_SET_ADDR 0x0001        // Set device address
#define MT_SET_DATETIME 0x0002    // Set device date and time
#define MT_INIT_STORAGE 0x0003    // Initialise storage
#define MT_GET_STATUS 0x0004      // Get device status
#define MT_FLASH_DUMP_PAGE 0x0008 // Dump flash page
#define MT_FLASH_RESET 0x0010     // Reset the flash
#define MT_NOK 0x4000             // Not OK
#define MT_OK 0x8000              // OK

#define DT_KIND_UNKNOWN 0x00
#define DT_KIND_UTC 0x01
#define DT_KIND_LOCAL 0x02

#endif // __PROTOCOL_H__
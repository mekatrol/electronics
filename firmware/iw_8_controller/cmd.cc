#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../common/communication/tty.h"
#include "../common/storage/flash_w25q128.h"
#include "../common/memory/memory.h"
#include "cmd.h"
#include "controller_init.h"
#include "flows.h"

#define CMD_ROOT_CMD_NONE 0
#define CMD_ROOT_CMD_HELP 1
#define CMD_ROOT_CMD_VER 2
#define CMD_ROOT_CMD_FLASH_ERASE 3
#define CMD_ROOT_CMD_FLASH_RESET 4
#define CMD_ROOT_CMD_FLASH_DUMP 5
#define CMD_ROOT_CMD_FLASH_READ_MANUFACTURER_ID 6
#define CMD_ROOT_CMD_FLASH_READ_UNIQUE_ID 7
#define CMD_ROOT_CMD_FLOWS_DUMP 8
#define CMD_ROOT_CMD_MEMORY 9
#define CMD_ROOT_CMD_UNK (~0)

#define CMD_HELP_STR "?"
#define CMD_VER_STR "ver"
#define CMD_FLASH_DUMP_STR "flash dump"
#define CMD_FLASH_ERASE_STR "flash erase"
#define CMD_FLASH_RESET_STR "flash reset"
#define CMD_FLASH_READ_MANUFACTURER_ID_STR "flash read manufacturerid"
#define CMD_FLASH_READ_UNIQUE_ID_STR "flash read uniqueid"
#define CMD_FLOWS_DUMP_STR "flows dump"
#define CMD_MEMORY_STR "memory"

const int CMD_FLASH_DUMP_STR_LEN = strlen(CMD_FLASH_DUMP_STR);

extern FlashStorage storage;

void cmd_print_help();
void cmd_flash_dump_page(const char *command_line);
void cmd_flash_erase();
void cmd_flash_read_manufacturer_id();
void cmd_flash_read_unique_id();
void cmd_flash_reset();
void cmd_memory_dump();

uint16_t cmd_get_root_command(char *command_line)
{
  if (strlen(command_line) == 0)
  {
    return CMD_ROOT_CMD_NONE;
  }

  if (strncmp(command_line, CMD_HELP_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_HELP;
  }

  if (strncmp(command_line, CMD_VER_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_VER;
  }

  if (strncmp(command_line, CMD_FLASH_ERASE_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_FLASH_ERASE;
  }

  if (strncmp(command_line, CMD_FLASH_READ_MANUFACTURER_ID_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_FLASH_READ_MANUFACTURER_ID;
  }

  if (strncmp(command_line, CMD_FLASH_READ_UNIQUE_ID_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_FLASH_READ_UNIQUE_ID;
  }

  if (strncmp(command_line, CMD_FLASH_RESET_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_FLASH_RESET;
  }

  if (strncmp(command_line, CMD_FLASH_DUMP_STR, CMD_FLASH_DUMP_STR_LEN) == 0)
  {
    return CMD_ROOT_CMD_FLASH_DUMP;
  }

  if (strncmp(command_line, CMD_FLOWS_DUMP_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_FLOWS_DUMP;
  }

  if (strncmp(command_line, CMD_MEMORY_STR, TTY_BUFFER_SIZE) == 0)
  {
    return CMD_ROOT_CMD_MEMORY;
  }

  return CMD_ROOT_CMD_UNK;
}

void cmd_process_command_line(char *command_line)
{
  uint16_t command = cmd_get_root_command(command_line);

  switch (command)
  {
  case CMD_ROOT_CMD_NONE:
    // Do nothing for no command
    return;

  case CMD_ROOT_CMD_HELP:
    cmd_print_help();
    return;

  case CMD_ROOT_CMD_VER:
    printf("IW8 ver: %d.%d.%d.%d\r\n", 0, 1, 0, 0);
    return;

  case CMD_ROOT_CMD_FLASH_ERASE:
    cmd_flash_erase();
    return;

  case CMD_ROOT_CMD_FLASH_READ_MANUFACTURER_ID:
    cmd_flash_read_manufacturer_id();
    return;

  case CMD_ROOT_CMD_FLASH_READ_UNIQUE_ID:
    cmd_flash_read_unique_id();
    return;

  case CMD_ROOT_CMD_FLASH_RESET:
    cmd_flash_reset();
    return;

  case CMD_ROOT_CMD_FLASH_DUMP:
    cmd_flash_dump_page(command_line);
    return;

  case CMD_ROOT_CMD_FLOWS_DUMP:
    flows_dump_list();
    return;

  case CMD_ROOT_CMD_MEMORY:
    cmd_memory_dump();
    return;

  default:
    printf("Unknown command '%s'\r\n", command_line);
    return;
  }
}

void cmd_memory_dump()
{
  printf("Total: %d bytes, allocated: %d bytes, available %d bytes\r\n", memory_get_total(), memory_get_allocated(), memory_get_available());
}

void cmd_flash_dump_page(const char *command_line)
{
  // There must be a space following the command
  if (command_line[CMD_FLASH_DUMP_STR_LEN] != ' ')
  {
    printf("Unknown command '%s'\r\n", command_line);
    return;
  }

  const int len = strlen(command_line);
  const char *page_addr_str = &command_line[CMD_FLASH_DUMP_STR_LEN + 1];

  uint16_t page_addr = atoi(page_addr_str);

  storage.DumpPage(page_addr);
}

void cmd_flash_erase()
{
  printf("Erasing the flash.\r\n");

  // Erase the chip
  storage.ChipErase();

  printf("Flash erased.\r\n");
}

void cmd_flash_read_manufacturer_id()
{
  printf("Manufacturer ID: %04x\r\n", storage.ReadManufacturerId());
}

void cmd_flash_read_unique_id()
{
  printf("Device unique ID: %08x\r\n", storage.ReadDeviceUniqueId());
}

void cmd_flash_reset()
{
  const uint32_t page_addr = 0;
  uint8_t page_buf[EXT_FLASH_PAGE_SIZE];

  printf("Resetting the flash.\r\n");

  // Reset flash
  controller_init_reset_flash(page_addr, page_buf);

  // Read first page after initialising
  storage.Read(page_addr, page_buf, EXT_FLASH_PAGE_SIZE);

  if (!controller_flash_is_initialised(page_buf))
  {
    // Show fail response
    printf("Failed to initialise the flash.\r\n");
    return;
  }

  printf("Flash initialised.\r\n");
}

void cmd_print_help()
{
  printf("commands:\r\n");
  printf("  %s - display available commands.\r\n", CMD_HELP_STR);
  printf("  %s - get controller version.\r\n", CMD_VER_STR);

  printf("  %s - get memory status.\r\n", CMD_MEMORY_STR);

  printf("  %s - erase the flash.\r\n", CMD_FLASH_ERASE_STR);
  printf("  %s - read manufacturer / device ID.\r\n", CMD_FLASH_READ_MANUFACTURER_ID_STR);
  printf("  %s - read device unique ID.\r\n", CMD_FLASH_READ_UNIQUE_ID_STR);
  printf("  %s - reset flash to default values.\r\n", CMD_FLASH_RESET_STR);
  printf("  %s N - dump external flash page, where N is the page number to dump.\r\n", CMD_FLASH_DUMP_STR);
}

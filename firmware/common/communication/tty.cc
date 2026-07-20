#include "tty.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define PICO_TARGET_STDIO_USB

#ifdef PICO_TARGET_STDIO_USB
#include "tusb.h"
#else
#endif

static char tty_buffer[TTY_BUFFER_SIZE];
static uint16_t tty_buffer_index = 0;

void tty_echo(char ch);
uint16_t tty_process_line(char *line);
bool tty_check_line_available();

uint16_t tty_tick(char *line)
{
  if (tty_check_line_available())
  {
    return tty_process_line(line);
  }

  return 0;
}

bool tty_check_line_available()
{
#ifdef PICO_TARGET_STDIO_USB
  if (!stdio_usb_connected())
  {
    return false;
  }

  // Get the number of bytes available to read from USB terminal
  uint32_t usb_bytes_available = tud_cdc_available();
#else

  uint32_t usb_bytes_available = uart_is_readable(uart1);
#endif

  // Read each byte available
  while (usb_bytes_available-- > 0)
  {
    // Get and echo next char
    char ch = getchar();

    if (ch == '\b' || ch == 0x7F) // Backspace or delete
    {
      if (tty_buffer_index > 0)
      {
        tty_buffer[tty_buffer_index--] = '\0';

        // Echo the received character
        tty_echo(ch);
      }

      continue;
    }

    // Echo the received character
    tty_echo(ch);

    // Return character?
    if (ch == '\r')
    {
      // Line is available (no need to store character in buffer)
      return true;
    }

    // Append character
    tty_buffer[tty_buffer_index] = ch;

    // If reached end of buffer rollover to index start
    if (++tty_buffer_index >= TTY_BUFFER_SIZE)
    {
      tty_buffer_index = 0;

      tty_prompt();
      return false;
    }

    // Null terminate
    tty_buffer[tty_buffer_index] = '\0';
  }

  return false;
}

void tty_echo(char ch)
{
  printf("%c", ch);
  if (ch == '\r')
  {
    printf("%c", '\n');
  }
}

void tty_prompt()
{
  printf("IW8> ");
}

bool tty_iswhitespace(char ch)
{
  return ch == ' ' ||  // space charcter
         ch == '\t' || // horizontal tab character
         ch == '\v' || // vertical tab character
         ch == '\f' || // form feed character
         ch == '\r' || // carriage return character
         ch == '\n';   // newline character (line feed)
}

uint16_t tty_process_line(char *line)
{
  // Trim any whitespace from end of the command
  while (tty_buffer_index > 0 && tty_iswhitespace(tty_buffer[tty_buffer_index]))
  {
    tty_buffer[tty_buffer_index] = '\0';
    tty_buffer_index--;
  }

  if (tty_buffer_index == 0)
  {
    // Simply send prompt
    tty_prompt();
    return 0;
  }

  // Get line length
  uint16_t len = strnlen(tty_buffer, TTY_BUFFER_SIZE - 1);

  // Copy command to line
  strncpy(line, tty_buffer, len);

  // Make sure null terminated
  line[len] = '\0';

  // Reset buffer
  tty_buffer_index = 0;

  return len;
}
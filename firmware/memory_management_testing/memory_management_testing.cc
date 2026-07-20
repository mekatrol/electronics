#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"

#include "../common/memory/memory.h"

#define TEST_MEMORY

static inline size_t memory_align_up_(size_t size, size_t align)
{
  return (((size) + ((align)-1)) & ~((align)-1));
}

void fail()
{
  gpio_init(PICO_DEFAULT_LED_PIN);
  gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);

  while (true)
  {
    // Flash LED rapidly
    sleep_ms(100);
    gpio_put(PICO_DEFAULT_LED_PIN, 0);
    sleep_ms(100);
    gpio_put(PICO_DEFAULT_LED_PIN, 1);
  }
}

// Linker definitions for heap
extern char __StackLimit;
extern size_t __end__;

int main()
{
  // Initialize all of the present standard stdio types that are linked into the binary.
  stdio_init_all();

  // Initialise memory before anything else
  memory_init((void *)&__end__, (size_t)&__StackLimit - (size_t)&__end__);

#ifdef TEST_MEMORY

  size_t memory_total = memory_get_total();

  if (memory_get_available() != memory_total)
  {
    fail();
  }

  if (memory_get_allocated() != 0)
  {
    fail();
  }

  if (memory_get_free_node_count() != 1)
  {
    fail();
  }

  if (memory_get_calculated_available() != memory_total)
  {
    fail();
  }

  void *cant_do = malloc(300000);

  if (cant_do)
  {
    fail();
  }

  void *can_do = malloc(memory_align_up_(memory_total - 12, 4) - 12);

  if (!can_do)
  {
    fail();
  }

  free(can_do);

  void *pointers[30] = {};

  size_t sizes[30] = {
      100,
      200,
      1000,
      45,
      99,
      55,
      30000,
      100000,
      1,
      101,
      100,
      200,
      1000,
      45,
      99,
      55,
      30000,
      10000,
      1,
      101,
      100,
      200,
      1000,
      45,
      99,
      55,
      30000,
      1000,
      1,
      101};

  size_t total_size = 0;
  for (int i = 0; i < 30; i++)
  {
    size_t size = sizes[i];

    pointers[i] = malloc(size);
    memset(pointers[i], 0xA5, size);

    size_t expected_allocated = memory_align_up_(size, sizeof(void *)) + 12; // memory requested plus node header
    size_t allocated = memory_get_allocated();

    total_size += expected_allocated;

    if (total_size != allocated)
    {
      fail();
    }
  }

  for (int i = 0; i < 30; i += 2)
  {
    free(pointers[i]);
    pointers[i] = nullptr;
    total_size -= memory_align_up_(sizes[i], sizeof(void *)) + 12;
  }

  size_t calc_allocated = memory_total - memory_get_calculated_available();
  size_t allocated = memory_get_allocated();
  if (allocated != total_size || allocated != calc_allocated)
  {
    fail();
  }

  size_t free_node_count = memory_get_free_node_count();
  if (free_node_count != 16) // The 15 nodes that were freed + 1 free node that was always available
  {
    fail();
  }

  for (int i = 0; i < 30; i++)
  {
    if (pointers[i])
    {
      free(pointers[i]);
    }
  }

  if (memory_get_available() != memory_total)
  {
    fail();
  }

  if (memory_get_calculated_available() != memory_total)
  {
    fail();
  }

  if (memory_get_free_node_count() != 1)
  {
    fail();
  }

#endif // TEST_MEMORY

  gpio_init(PICO_DEFAULT_LED_PIN);
  gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);

  while (true)
  {
    sleep_ms(1000);
    gpio_put(PICO_DEFAULT_LED_PIN, 0);
    sleep_ms(1000);
    gpio_put(PICO_DEFAULT_LED_PIN, 1);
  }
}
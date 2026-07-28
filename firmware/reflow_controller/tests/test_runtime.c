#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "runtime_scheduler.h"
#include "runtime_work_queue.h"

static uint8_t calls[8];
static uint8_t call_count;

static void high_task(void)
{
  calls[call_count++] = 1u;
}

static void low_task(void)
{
  calls[call_count++] = 2u;
}

static void work(uint32_t argument)
{
  calls[call_count++] = (uint8_t)argument;
}

int main(void)
{
  runtime_task_t tasks[] = {
      {low_task, 10u, 0u, 5u, true},
      {high_task, 5u, 0u, 1u, true},
  };
  runtime_scheduler_t scheduler = {tasks, 2u};
  runtime_work_item_t storage[2];
  runtime_work_queue_t queue;

  runtime_scheduler_initialize(&scheduler, 100u);
  runtime_scheduler_run_once(&scheduler, 100u);
  assert(call_count == 2u && calls[0] == 1u && calls[1] == 2u);
  runtime_scheduler_run_once(&scheduler, 104u);
  assert(call_count == 2u);
  runtime_scheduler_run_once(&scheduler, 105u);
  assert(call_count == 3u && calls[2] == 1u);

  call_count = 0u;
  runtime_work_queue_initialize(&queue, storage, 2u);
  assert(runtime_work_queue_push(
      &queue, (runtime_work_item_t){work, 3u}));
  assert(runtime_work_queue_push(
      &queue, (runtime_work_item_t){work, 4u}));
  assert(!runtime_work_queue_push(
      &queue, (runtime_work_item_t){work, 5u}));
  assert(runtime_work_queue_run_one(&queue));
  assert(runtime_work_queue_run_one(&queue));
  assert(!runtime_work_queue_run_one(&queue));
  assert(call_count == 2u && calls[0] == 3u && calls[1] == 4u);
  return 0;
}

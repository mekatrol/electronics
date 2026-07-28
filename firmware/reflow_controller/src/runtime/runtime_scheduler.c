#include "runtime_scheduler.h"

static bool time_reached(uint32_t now, uint32_t deadline)
{
  return (int32_t)(now - deadline) >= 0;
}

void runtime_scheduler_initialize(runtime_scheduler_t *scheduler,
                                  uint32_t now_milliseconds)
{
  for (uint8_t index = 0u; index < scheduler->task_count; index++)
  {
    scheduler->tasks[index].next_run_milliseconds = now_milliseconds;
  }
}

void runtime_scheduler_run_once(runtime_scheduler_t *scheduler,
                                uint32_t now_milliseconds)
{
  for (uint16_t priority = 0u; priority <= 255u; priority++)
  {
    for (uint8_t index = 0u; index < scheduler->task_count; index++)
    {
      runtime_task_t *const task = &scheduler->tasks[index];
      if (task->enabled && task->priority == priority &&
          time_reached(now_milliseconds, task->next_run_milliseconds))
      {
        /* Reschedule before calling so a callback can never re-enter itself. */
        task->next_run_milliseconds =
            now_milliseconds + task->period_milliseconds;
        task->callback();
      }
    }
  }
}

#ifndef REFLOW_RUNTIME_SCHEDULER_H
#define REFLOW_RUNTIME_SCHEDULER_H

#include <stdbool.h>
#include <stdint.h>

typedef void (*runtime_task_callback_t)(void);

typedef struct
{
  runtime_task_callback_t callback;
  uint32_t period_milliseconds;
  uint32_t next_run_milliseconds;
  uint8_t priority;
  bool enabled;
} runtime_task_t;

typedef struct
{
  runtime_task_t *tasks;
  uint8_t task_count;
} runtime_scheduler_t;

void runtime_scheduler_initialize(runtime_scheduler_t *scheduler,
                                  uint32_t now_milliseconds);
void runtime_scheduler_run_once(runtime_scheduler_t *scheduler,
                                uint32_t now_milliseconds);

#endif

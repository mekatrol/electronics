#ifndef REFLOW_RUNTIME_WORK_QUEUE_H
#define REFLOW_RUNTIME_WORK_QUEUE_H

#include <stdbool.h>
#include <stdint.h>

typedef void (*runtime_work_callback_t)(uint32_t argument);

typedef struct
{
  runtime_work_callback_t callback;
  uint32_t argument;
} runtime_work_item_t;

typedef struct
{
  runtime_work_item_t *items;
  uint8_t capacity;
  uint8_t read_index;
  uint8_t count;
} runtime_work_queue_t;

void runtime_work_queue_initialize(runtime_work_queue_t *queue,
                                   runtime_work_item_t *storage,
                                   uint8_t capacity);
bool runtime_work_queue_push(runtime_work_queue_t *queue,
                             runtime_work_item_t item);
bool runtime_work_queue_run_one(runtime_work_queue_t *queue);

#endif

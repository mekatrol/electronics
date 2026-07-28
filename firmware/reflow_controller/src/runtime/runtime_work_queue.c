#include "runtime_work_queue.h"

void runtime_work_queue_initialize(runtime_work_queue_t *queue,
                                   runtime_work_item_t *storage,
                                   uint8_t capacity)
{
  queue->items = storage;
  queue->capacity = capacity;
  queue->read_index = 0u;
  queue->count = 0u;
}

bool runtime_work_queue_push(runtime_work_queue_t *queue,
                             runtime_work_item_t item)
{
  uint8_t write_index;
  if (queue->count == queue->capacity)
  {
    return false;
  }
  write_index = (uint8_t)((queue->read_index + queue->count) % queue->capacity);
  queue->items[write_index] = item;
  queue->count++;
  return true;
}

bool runtime_work_queue_run_one(runtime_work_queue_t *queue)
{
  runtime_work_item_t item;
  if (queue->count == 0u)
  {
    return false;
  }
  item = queue->items[queue->read_index];
  queue->read_index = (uint8_t)((queue->read_index + 1u) % queue->capacity);
  queue->count--;
  item.callback(item.argument);
  return true;
}

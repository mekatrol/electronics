#ifndef REFLOW_FAT_VOLUME_H
#define REFLOW_FAT_VOLUME_H

#include <stdbool.h>
#include <stdint.h>

typedef struct
{
  uint32_t partition_start_block;
  uint32_t fat_start_block;
  uint32_t data_start_block;
  uint32_t root_cluster;
  uint32_t sectors_per_fat;
  uint16_t bytes_per_sector;
  uint8_t sectors_per_cluster;
  uint8_t fat_count;
  bool mounted;
} fat_volume_t;

bool fat_volume_mount(fat_volume_t *volume);
bool fat_volume_read_root_sector(const fat_volume_t *volume,
                                 uint8_t *destination);

#endif

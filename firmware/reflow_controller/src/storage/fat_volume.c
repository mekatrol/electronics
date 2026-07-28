#include <stdbool.h>
#include <stdint.h>

#include "fat_volume.h"
#include "sd_card.h"

static uint8_t sector[512];

static uint16_t read_u16(uint8_t const *source)
{
  return (uint16_t)source[0] | ((uint16_t)source[1] << 8u);
}

static uint32_t read_u32(uint8_t const *source)
{
  return (uint32_t)source[0] | ((uint32_t)source[1] << 8u) |
         ((uint32_t)source[2] << 16u) | ((uint32_t)source[3] << 24u);
}

bool fat_volume_mount(fat_volume_t *volume)
{
  uint32_t partition_start = 0u;
  uint16_t reserved;
  if (!sd_card_read_block(0u, sector) || read_u16(&sector[510]) != 0xAA55u)
  {
    return false;
  }
  if ((sector[450] == 0x0Bu) || (sector[450] == 0x0Cu))
  {
    partition_start = read_u32(&sector[454]);
    if (!sd_card_read_block(partition_start, sector))
    {
      return false;
    }
  }
  volume->bytes_per_sector = read_u16(&sector[11]);
  volume->sectors_per_cluster = sector[13];
  reserved = read_u16(&sector[14]);
  volume->fat_count = sector[16];
  volume->sectors_per_fat = read_u32(&sector[36]);
  volume->root_cluster = read_u32(&sector[44]);
  if ((volume->bytes_per_sector != 512u) ||
      (volume->sectors_per_cluster == 0u) ||
      (volume->fat_count == 0u) ||
      (volume->sectors_per_fat == 0u) ||
      (volume->root_cluster < 2u))
  {
    return false;
  }
  volume->partition_start_block = partition_start;
  volume->fat_start_block = partition_start + reserved;
  volume->data_start_block =
      volume->fat_start_block +
      ((uint32_t)volume->fat_count * volume->sectors_per_fat);
  volume->mounted = true;
  return true;
}

bool fat_volume_read_root_sector(const fat_volume_t *volume,
                                 uint8_t *destination)
{
  uint32_t block;
  if (!volume->mounted)
  {
    return false;
  }
  block = volume->data_start_block +
          ((volume->root_cluster - 2u) * volume->sectors_per_cluster);
  return sd_card_read_block(block, destination);
}

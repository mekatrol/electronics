#ifndef __FLASH_STORAGE_H__
#define __FLASH_STORAGE_H__

#include "pico/stdlib.h"

#include "hardware/spi.h"

#define EXT_FLASH_PAGE_SIZE 256
#define EXT_FLASH_SECTOR_SIZE 4096

class FlashStorage
{
public:
    FlashStorage(spi_inst_t *spi, uint cs_pin, uint clk_pin, uint rx_pin, uint tx_pin);
    ~FlashStorage();

    uint32_t ReadManufacturerId();
    uint64_t ReadDeviceUniqueId();
    void Read(uint32_t addr, uint8_t *buf, size_t len);
    void ChipErase();
    void SectorErase(uint32_t sector_addr);
    void PageProgram(uint32_t page_addr, uint8_t data_buf[]);

    void DumpPage(uint16_t page_addr);

private:
    spi_inst_t *spi;
    uint cs_pin;
    uint clk_pin;
    uint rx_pin;
    uint tx_pin;

    void WaitTillNotBusy();
    inline void ChipSelect();
    inline void ChipDeselect();

    void WriteEnable();
};

#endif // __FLASH_STORAGE_H__
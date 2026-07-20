#include <stdio.h>

#include "hardware/spi.h"

#include "flash_w25q128.h"

#define FLASH_CMD_PAGE_PROGRAM 0x02
#define FLASH_CMD_READ 0x03

#define FLASH_CMD_STATUS_1 0x05
#define FLASH_CMD_STATUS_2 0x05
#define FLASH_CMD_STATUS_3 0x05

#define FLASH_CMD_WRITE_EN 0x06

#define FLASH_CMD_SECTOR_ERASE 0x20
#define FLASH_CMD_CHIP_ERASE 0x60 // Note can also be 0xC7

#define FLASH_CMD_READ_MANUFACTURER_ID 0x90
#define FLASH_CMD_READ_UNIQUE_ID 0x4B

// Status Register 1 - Bit masks
#define FLASH_STATUS_BUSY_MASK 0x01                // Busy
#define FLASH_STATUS_WEL_MASK 0x02                 // Write Enable Latch
#define FLASH_STATUS_BPB_MASK (0x04 | 0x08 | 0x10) // Block Protect
#define FLASH_STATUS_TBP_MASK 0x20                 // Top / Bottom Protect
#define FLASH_STATUS_SP_MASK 0x40                  // Sector Protect
#define FLASH_STATUS_1_RES_0x80_MASK 0x80          // Reserved

// Status Register 2 - Bit masks
#define FLASH_STATUS_SRL_MASK 0x01                  // Status Register Lock
#define FLASH_STATUS_QE_MASK 0x02                   // Quad Enable
#define FLASH_STATUS_2_RES_0x40_MASK 0x40           // Reserved
#define FLASH_STATUS_SRLB_MASK (0x08 | 0x10 | 0x20) // Security Register Lock
#define FLASH_STATUS_CMP_MASK 0x40                  // Complement Protect
#define FLASH_STATUS_SUS_MASK 0x80                  // Suspend Status

// Status Register 3 - Bit masks
#define FLASH_STATUS_3_RES_0x01_MASK 0x01   // Reserved
#define FLASH_STATUS_3_RES_0x02_MASK 0x02   // Reserved
#define FLASH_STATUS_WPS_MASK 0x04          // Write Protect Selection
#define FLASH_STATUS_3_RES_0x08_MASK 0x08   // Reserved
#define FLASH_STATUS_3_RES_0x10_MASK 0x10   // Reserved
#define FLASH_STATUS_ODS_MASK (0x20 | 0x40) // Output Driver Strength
#define FLASH_STATUS_3_RES_0x80_MASK 0x80   // Reserved

// Output Driver Strength DRV1, DRV0
#define ODS_100_PCT 0x00 // 100%
#define ODS_75_PCT 0x01  // 75%
#define ODS_50_PCT 0x02  // 50%
#define ODS_25_PCT 0x03  // 25% (Default)

FlashStorage::FlashStorage(
    spi_inst_t *spi,
    uint cs_pin,
    uint clk_pin,
    uint rx_pin,
    uint tx_pin)
{
    this->spi = spi;
    this->cs_pin = cs_pin;
    this->clk_pin = clk_pin;
    this->rx_pin = rx_pin;
    this->tx_pin = tx_pin;

    // Init SPI0 at 1MHz
    spi_init(this->spi, 1000 * 1000);

    // Set SPI0 to alternate pins
    gpio_set_function(this->cs_pin, GPIO_FUNC_SPI);
    gpio_set_function(this->clk_pin, GPIO_FUNC_SPI);
    gpio_set_function(this->rx_pin, GPIO_FUNC_SPI);
    gpio_set_function(this->tx_pin, GPIO_FUNC_SPI);

    // Make SPI CS high
    gpio_init(this->cs_pin);
    gpio_put(this->cs_pin, 1);
    gpio_set_dir(this->cs_pin, GPIO_OUT);
}

FlashStorage::~FlashStorage()
{
}

void __not_in_flash_func(FlashStorage::DumpPage)(uint16_t page_addr)
{
    // Multiple by 256 to get byte offset
    uint32_t byte_offset = page_addr << 8;

    uint8_t buf[EXT_FLASH_PAGE_SIZE];

    printf("page number: %d (%04x)\n", page_addr, page_addr);

    Read(byte_offset, buf, EXT_FLASH_PAGE_SIZE);

    for (int i = 0; i < EXT_FLASH_PAGE_SIZE; ++i)
    {
        if (i % 16 == 15)
        {
            printf("%02x\n", buf[i]);
        }
        else
        {
            printf("%02x ", buf[i]);
        }
    }
}

void __not_in_flash_func(FlashStorage::Read)(uint32_t addr, uint8_t *buf, size_t len)
{
    uint8_t cmd_buf[4] = {
        FLASH_CMD_READ,
        (uint8_t)(addr >> 16),
        (uint8_t)(addr >> 8),
        (uint8_t)(addr & 0xFF)};

    ChipSelect();
    spi_write_blocking(spi, cmd_buf, 4);
    spi_read_blocking(spi, 0, buf, len);
    ChipDeselect();
}

uint32_t __not_in_flash_func(FlashStorage::ReadManufacturerId)()
{
    uint8_t cmd_buf[4] = {
        FLASH_CMD_READ_MANUFACTURER_ID,
        0,
        0,
        0};

    uint8_t value[2];

    ChipSelect();
    spi_write_blocking(spi, cmd_buf, 4);
    spi_read_blocking(spi, 0, value, 2);
    ChipDeselect();

    return value[0] << 8 | value[1];
}

uint64_t __not_in_flash_func(FlashStorage::ReadDeviceUniqueId)()
{
    uint8_t cmd_buf[5] = {
        FLASH_CMD_READ_UNIQUE_ID,
        0,
        0,
        0,
        0};

    uint8_t value[4];

    ChipSelect();
    spi_write_blocking(spi, cmd_buf, 5);
    spi_read_blocking(spi, 0, value, 8);
    ChipDeselect();

    uint64_t id = (uint64_t)value[7] << 56UL | (uint64_t)value[6] << 48UL | (uint64_t)value[5] << 40UL | (uint64_t)(uint64_t)value[4] << 32UL |
                  (uint64_t)value[3] << 24UL | (uint64_t)value[2] << 16UL | (uint64_t)value[1] << 8UL | (uint64_t)(uint64_t)value[0];

    return id;
}

void __not_in_flash_func(FlashStorage::ChipErase)()
{
    uint8_t cmd_buf[1] = {
        FLASH_CMD_CHIP_ERASE};

    uint8_t value[4];

    WriteEnable();
    ChipSelect();
    spi_write_blocking(spi, cmd_buf, 1);
    ChipDeselect();
    WaitTillNotBusy();
}

void __not_in_flash_func(FlashStorage::SectorErase)(uint32_t sector_addr)
{
    uint8_t cmd_buf[4] = {
        (uint8_t)(FLASH_CMD_SECTOR_ERASE),
        (uint8_t)(sector_addr >> 16),
        (uint8_t)(sector_addr >> 8),
        (uint8_t)(sector_addr & 0xFF)};

    WriteEnable();
    ChipSelect();
    spi_write_blocking(spi, cmd_buf, 4);
    ChipDeselect();
    WaitTillNotBusy();
}

void __not_in_flash_func(FlashStorage::PageProgram)(uint32_t page_addr, uint8_t data_buf[])
{
    uint8_t cmd_buf[4] = {
        (uint8_t)(FLASH_CMD_PAGE_PROGRAM),
        (uint8_t)(page_addr >> 16),
        (uint8_t)(page_addr >> 8),
        (uint8_t)(page_addr & 0xFF)};

    WriteEnable();
    ChipSelect();
    spi_write_blocking(spi, cmd_buf, 4);
    spi_write_blocking(spi, data_buf, EXT_FLASH_PAGE_SIZE);
    ChipDeselect();
    WaitTillNotBusy();
}

void __not_in_flash_func(FlashStorage::WriteEnable)()
{
    uint8_t cmd = FLASH_CMD_WRITE_EN;

    ChipSelect();
    spi_write_blocking(spi, &cmd, 1);
    ChipDeselect();
}

void __not_in_flash_func(FlashStorage::WaitTillNotBusy)()
{
    uint8_t status;

    // Loop until busy mask reset
    do
    {
        // Set on each loop as we also use as receive buffer
        uint8_t buf[2] = {FLASH_CMD_STATUS_1, 0};

        ChipSelect();
        spi_write_read_blocking(spi, buf, buf, 2);
        ChipDeselect();

        // Get status
        status = buf[1];
    } while (status & FLASH_STATUS_BUSY_MASK);
}

inline void FlashStorage::ChipSelect()
{
    gpio_put(cs_pin, 0);
}

inline void FlashStorage::ChipDeselect()
{
    gpio_put(cs_pin, 1);
}

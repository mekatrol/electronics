add_executable(iw_8_controller)

set(PICO_UART_ENABLE_CRLF_SUPPORT 0)
set(PICO_TARGET_STDIO_USB 1)

pico_generate_pio_header(iw_8_controller ${PROJECT_SOURCE_DIR}/common/pio/74hc595.pio)

target_sources(iw_8_controller PRIVATE 
    iw_8_controller.cc
    cmd.cc
    controller_init.cc
    flows.cc
    messaging.cc
    state.cc
    ../common/communication/buffer.cc
    ../common/communication/message.cc
    ../common/communication/serial.cc
    ../common/communication/tty.cc
    ../common/memory/memory.cc
    ../common/rtc/ds1307.cc
    ../common/storage/flash_pico.cc
    ../common/storage/flash_w25q128.cc
    ../common/utils/core_sync.cc
    ../common/utils/ascii.cc
    ../common/utils/bcd.cc
    ../common/utils/crc16.cc
    ../common/utils/debug.cc
    ../common/utils/i2c_util.cc
    ../common/utils/intercore_queue.cc
    ../common/utils/linked_list.cc
    )

# pull in common dependencies
target_link_libraries(iw_8_controller PRIVATE 
    pico_stdlib 
    pico_multicore
    hardware_gpio 
    hardware_pio 
    hardware_rtc
    hardware_flash
    hardware_spi
    hardware_sync
    hardware_i2c
    hardware_adc
    # picow_wifi_scan_poll
    # picow_wifi_scan_background
    # pico_cyw43_arch_lwip_poll
    # pico_cyw43_arch_lwip_threadsafe_background
    -Wl,--wrap=malloc,--wrap=free,--wrap=calloc,--wrap=realloc
    )

# Enable usb output for stdio
pico_enable_stdio_usb(iw_8_controller 1)

# Disable uart output for stdio
pico_enable_stdio_uart(iw_8_controller 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(iw_8_controller)

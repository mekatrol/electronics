add_executable(uart_testing)

target_sources(uart_testing PRIVATE 
    uart_testing.cc
    ../common/communication/serial.cc
    ../common/memory/memory.cc
    )

# pull in common dependencies
target_link_libraries(uart_testing PRIVATE 
    pico_stdlib 
    pico_multicore
    hardware_gpio 
    -Wl,--wrap=malloc,--wrap=free,--wrap=calloc,--wrap=realloc
    )

# Enable usb output for stdio
pico_enable_stdio_usb(uart_testing 0)

# Disable uart output for stdio
pico_enable_stdio_uart(uart_testing 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(uart_testing)

add_executable(memory_management_testing)

target_sources(memory_management_testing PRIVATE 
    memory_management_testing.cc
    ../common/memory/memory.cc
    )

# pull in common dependencies
target_link_libraries(memory_management_testing PRIVATE 
    pico_stdlib 
    pico_multicore
    -Wl,--wrap=malloc,--wrap=free,--wrap=calloc,--wrap=realloc
    )

# Enable usb output for stdio
pico_enable_stdio_usb(memory_management_testing 0)

# Disable uart output for stdio
pico_enable_stdio_uart(memory_management_testing 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(memory_management_testing)

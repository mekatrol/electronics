cmake_minimum_required(VERSION 3.12)

set(PICO_BOARD pico_w)

set(PICO 1)
set(SKIP_PICO_MALLOC 1)

# Pull in SDK (must be before project)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(home_automation C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

if (PICO_SDK_VERSION_STRING VERSION_LESS "1.3.0")
    message(FATAL_ERROR "Raspberry Pi Pico SDK version 1.3.0 (or later) required. Current version is ${PICO_SDK_VERSION_STRING}")
endif()

set(PICO_PATH ${PROJECT_SOURCE_DIR})

# Initialize the SDK
pico_sdk_init()

# Add product instances
add_subdirectory(iw_8_controller)
add_subdirectory(memory_management_testing)
add_subdirectory(uart_testing)


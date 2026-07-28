# Reflow controller firmware build.
# GNU Make and Arm GNU Toolchain are required on both Windows and Linux.

TOOLCHAIN_PREFIX ?= arm-none-eabi-
CC      := $(TOOLCHAIN_PREFIX)gcc
OBJCOPY := $(TOOLCHAIN_PREFIX)objcopy
SIZE    := $(TOOLCHAIN_PREFIX)size
OPENOCD ?= openocd
PYTHON ?= python3
HOST_CC ?= cc
STLINK_SERIAL ?=
OPENOCD_STLINK_SERIAL_CMD := $(if $(STLINK_SERIAL),-c "adapter serial $(STLINK_SERIAL)",)

PROJECT_NAME := reflow-controller

MAINBOARD_NAME := btt_skr_1_4_turbo

MAINBOARD_BUILD := build/mainboard/$(MAINBOARD_NAME)

MAINBOARD_ELF := $(MAINBOARD_BUILD)/$(PROJECT_NAME)-mainboard.elf
MAINBOARD_MAP := $(MAINBOARD_BUILD)/$(PROJECT_NAME)-mainboard.map
MAINBOARD_BIN := $(MAINBOARD_BUILD)/firmware.bin
HOST_RUNTIME_TEST := build/runtime-tests

MAINBOARD_SRCS_C := src/mainboard/main.c \
                    src/runtime/runtime_scheduler.c \
                    src/runtime/runtime_work_queue.c \
                    src/storage/sd_card.c \
                    src/storage/fat_volume.c \
                    boards/mainboard/mainboard_clock.c \
                    boards/mainboard/mainboard_gpio.c \
                    boards/mainboard/mainboard_hal.c \
                    boards/mainboard/mainboard_uart.c \
                    boards/mainboard/mainboard_temperature.c \
                    boards/mainboard/mainboard_spi.c \
                    boards/mainboard/mainboard_neopixel.c \
                    boards/display/mainboard_display_module.c
MAINBOARD_SRCS_S := boards/mainboard/startup.s

MAINBOARD_OBJS := $(patsubst %.c,$(MAINBOARD_BUILD)/%.o,$(MAINBOARD_SRCS_C)) \
                  $(patsubst %.s,$(MAINBOARD_BUILD)/%.o,$(MAINBOARD_SRCS_S))

CPUFLAGS := -mcpu=cortex-m3 -mthumb
COMMON_CFLAGS := $(CPUFLAGS) -std=c11 -Wall -Wextra -Werror -Os \
                 -ffreestanding -fdata-sections -ffunction-sections
COMMON_ASFLAGS := $(CPUFLAGS) -ffreestanding
COMMON_LDFLAGS := $(CPUFLAGS) -nostdlib -Wl,--gc-sections

MAINBOARD_CFLAGS := $(COMMON_CFLAGS) \
                    -Iboards/mainboard/include \
                    -Iboards/display \
                    -Isrc/runtime \
                    -Isrc/storage

MAINBOARD_LINKER := boards/mainboard/linker.ld

ifeq ($(OS),Windows_NT)
  define make_output_dir
	@if not exist "$(subst /,\,$(@D))" mkdir "$(subst /,\,$(@D))"
  endef
  define remove_build_dir
	@if exist "build" rmdir /S /Q "build"
  endef
else
  define make_output_dir
	@mkdir -p "$(@D)"
  endef
  define remove_build_dir
	@rm -rf "build"
  endef
endif

.DEFAULT_GOAL := all

.PHONY: all mainboard flash clean print-config toolchain-check test

all: mainboard

mainboard: $(MAINBOARD_BIN)
	$(SIZE) $(MAINBOARD_ELF)

toolchain-check:
	$(CC) --version
	$(OBJCOPY) --version
	$(SIZE) --version

test: $(HOST_RUNTIME_TEST)
	$(HOST_RUNTIME_TEST)

$(HOST_RUNTIME_TEST): tests/test_runtime.c \
                      src/runtime/runtime_scheduler.c \
                      src/runtime/runtime_work_queue.c
	$(call make_output_dir)
	$(HOST_CC) -std=c11 -Wall -Wextra -Werror -Isrc/runtime \
	  tests/test_runtime.c src/runtime/runtime_scheduler.c \
	  src/runtime/runtime_work_queue.c -o $@

# Program the raw application binary explicitly at 0x00004000. Do not pass an
# ELF to OpenOCD's LPC17xx "program" helper: it may treat the ELF container as
# raw bytes at address zero and overwrite the BTT bootloader.
flash: mainboard
	$(OPENOCD) -f interface/stlink.cfg $(OPENOCD_STLINK_SERIAL_CMD) -f target/lpc17xx.cfg -c "adapter speed 1000; init; reset halt; flash write_image erase $(abspath $(MAINBOARD_BIN)) 0x00004000 bin; verify_image $(abspath $(MAINBOARD_BIN)) 0x00004000 bin; reset run; shutdown"

$(MAINBOARD_BIN): $(MAINBOARD_ELF)
	$(OBJCOPY) -O binary $< $@
	$(PYTHON) tools/lpc_vector_checksum.py $@

$(MAINBOARD_ELF): $(MAINBOARD_OBJS) $(MAINBOARD_LINKER)
	$(call make_output_dir)
	$(CC) $(MAINBOARD_OBJS) $(COMMON_LDFLAGS) -Wl,-Map=$(MAINBOARD_MAP) -T$(MAINBOARD_LINKER) -o $@

$(MAINBOARD_BUILD)/%.o: %.c
	$(call make_output_dir)
	$(CC) $(MAINBOARD_CFLAGS) -c $< -o $@

$(MAINBOARD_BUILD)/%.o: %.s
	$(call make_output_dir)
	$(CC) $(COMMON_ASFLAGS) -c $< -o $@

clean:
	$(call remove_build_dir)

print-config:
	@echo PROJECT_NAME=$(PROJECT_NAME)
	@echo MAINBOARD_NAME=$(MAINBOARD_NAME)
	@echo CC=$(CC)
	@echo OPENOCD=$(OPENOCD)
	@echo PYTHON=$(PYTHON)
	@echo HOST_CC=$(HOST_CC)
	@echo STLINK_SERIAL=$(STLINK_SERIAL)
	@echo MAINBOARD_BIN=$(MAINBOARD_BIN)

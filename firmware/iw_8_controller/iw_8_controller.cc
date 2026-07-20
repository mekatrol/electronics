#include "pins.h"

#include <stdio.h>
#include <stdlib.h>

#include "pico/stdlib.h"
#include "pico/multicore.h"

#include "hardware/adc.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/pio.h"
#include "hardware/spi.h"
#include "hardware/i2c.h"

#include "../common/communication/message.h"
#include "../common/communication/protocol.h"
#include "../common/communication/serial.h"
#include "../common/communication/tty.h"

#include "../common/utils/core_sync.h"
#include "../common/utils/crc16.h"
#include "../common/utils/i2c_util.h"
#include "../common/memory/memory.h"

#include "cmd.h"
#include "controller_init.h"
#include "flows.h"
#include "state.h"
#include "messaging.h"

// Linker definitions for heap
extern char __StackLimit;
extern size_t __end__;

// Shift register references
extern PIO shift_register_pio;
extern uint shift_register_sm;

controller_config_t controller_config;
run_state_t run_state;

void core0_thread();
void core1_thread();

serial_conf_t serial0_config;
serial_conf_t serial1_config;
serial_conf_t *serial_main_config = &serial0_config;

int main()
{
    // Initialise memory before anything else, we set start and end address
    // of heap based on values set by linker
    memory_init((void *)&__end__, (size_t)&__StackLimit - (size_t)&__end__);

    // Controller startup, init flash, RTC, UART, I/O etc
    controller_init_startup();

    flow_functions = (flow_function_t *)malloc(FLOW_TYPE_TIME_SCHED * sizeof(flow_function_t));
    flow_function_t *ff = flow_functions;
    flow_function_t *prev = nullptr;
    for (int i = FLOW_TYPE_AVG; i <= FLOW_TYPE_TIME_SCHED; i++)
    {
        ff->type = i;
        ff->flags = 0;
        ff->next = nullptr;
        ff->data = nullptr;

        if (prev)
        {
            prev->next = ff;
        }

        prev = ff;
        ff = (ff + sizeof(flow_function_t));
    }

    flows_dump_list();

    // Initialise core synchronisation
    core_sync_init();

    // Serial 0 initialisation
    serial0_config.uart = uart0;
    serial0_config.baud_rate = 115200;
    serial0_config.send_enable_pin = UART0_DE_PIN;
    serial0_config.rx_pin = UART0_RX_PIN;
    serial0_config.tx_pin = UART0_TX_PIN;
    serial0_config.settings = SERIAL_ENABLE_MASK | SERIAL_SEND_ENABLE_SET | SERIAL_FROM_DATA_BITS(8) | SERIAL_FROM_STOP_BITS(1) | SERIAL_TO_PARITY(UART_PARITY_NONE);
    serial_init(&serial0_config);

    // Serial 1 initialisation
    serial1_config.uart = uart1;
    serial1_config.baud_rate = 115200;
    serial1_config.send_enable_pin = -1;
    serial1_config.rx_pin = UART1_RX_PIN;
    serial1_config.tx_pin = UART1_TX_PIN;
    serial1_config.settings = SERIAL_ENABLE_MASK | SERIAL_SEND_ENABLE_CLR | SERIAL_FROM_DATA_BITS(8) | SERIAL_FROM_STOP_BITS(1) | SERIAL_TO_PARITY(UART_PARITY_NONE);
    // serial_init(&uart1_config);

    multicore_launch_core1(core1_thread);
    core0_thread();

    return 0;
}

/**************************************************************************************************************
 * core 0 is used for communications processing
 **************************************************************************************************************/
#define LINE_BUFFER_SIZE 1024
#define RX_GET_CHAR_BUFFER_SIZE 1024
#define RX_BUFFER_SIZE 2048

void core0_thread()
{
    // Allocate a block of memory
    uint8_t *memory = (uint8_t *)malloc(LINE_BUFFER_SIZE + RX_GET_CHAR_BUFFER_SIZE + RX_BUFFER_SIZE);

    // Carve up into various buffers
    char *line = (char *)&memory[0];
    uint8_t *buffer = &memory[LINE_BUFFER_SIZE];
    uint8_t *rxBuffer = &memory[LINE_BUFFER_SIZE + RX_GET_CHAR_BUFFER_SIZE];
    uint16_t rxIndex = 0;

    // Core 0 forever loop
    while (true)
    {
        // Check for TTY data
        uint8_t len = tty_tick(line);

        // If TTY data then process as command line
        if (len > 0)
        {
            // Process the command line
            cmd_process_command_line(line);

            // Display prompt
            tty_prompt();
        }

        // Process main serial (uart)
        if (serial_has_rx_data(serial_main_config))
        {
            int count = serial_get_rx_data(serial_main_config, buffer, sizeof(buffer));

            for (int i = 0; i < count; i++)
            {
                uint8_t ch = buffer[i];

                if (ch == MSG_SOM)
                {
                    // MSG_SOM only ever occurs at begining of message so reset
                    // the receive index if found
                    rxIndex = 0;
                }
                else if (rxIndex == 0)
                {
                    // Need MSG_SOM to start, so ignore if waiting for SOM
                    continue;
                }

                rxBuffer[rxIndex++] = (uint8_t)ch;

                if (ch == MSG_EOM)
                {
                    process_rx_message(serial_main_config, rxBuffer, rxIndex);
                }
            }
        }

        bool inp1 = gpio_get(INP1_PIN);
        bool inp2 = gpio_get(INP2_PIN);
        bool adc0 = gpio_get(ADC0_PIN);
        bool adc1 = gpio_get(ADC1_PIN);
        bool adc2 = gpio_get(ADC2_PIN);

        // Get inputs state
        uint input_state = (adc2 ? 1 : 0) << 4 |
                           (adc1 ? 1 : 0) << 3 |
                           (adc0 ? 1 : 0) << 2 |
                           (inp2 ? 1 : 0) << 1 |
                           (inp1 ? 1 : 0) << 0;

        adc_select_input(0);
        uint16_t adc0v = adc_read();

        adc_select_input(1);
        uint16_t adc1v = adc_read();

        adc_select_input(2);
        uint16_t adc2v = adc_read();

        // Thread sync
        uint interrupt_status = core_sync_lock();

        // Copy ADC values
        run_state.adc0 = adc0v;
        run_state.adc1 = adc1v;
        run_state.adc2 = adc2v;

        // Copy input values
        run_state.inputs.state = input_state;

        // Release thread sync
        core_sync_unlock(interrupt_status);
    }

    // Will never happen (because of core 0 forever loop), but here for completeness
    free(memory);
}

/**************************************************************************************************************
 * core 1 is used for controller flows and logic
 **************************************************************************************************************/
void core1_thread()
{
    run_state_t *state = (run_state_t *)malloc(sizeof(run_state_t));

    // Core 1 forever loop
    while (true)
    {
        // Thread sync lock
        uint interrupt_status = core_sync_lock();

        // Get copy of current state
        memcpy(state, &run_state, sizeof(run_state_t));

        // Thread sync unlock
        core_sync_unlock(interrupt_status);

        if (state->inputs.state & 0x01)
        {
            gpio_put(LED_PIN, 1);
        }
        else
        {
            gpio_put(LED_PIN, 0);
        }

        // Routinely update output registers
        if (!pio_sm_is_tx_fifo_full(shift_register_pio, shift_register_sm))
        {
            // Get the initial state
            uint32_t outputs = run_state.outputs.state;

            // Enumerate output bits
            for (int i = 0; i < 32; i++)
            {
                // Set the bit position mask
                uint32_t bit_mask = 0x1 << i;

                // Is the overridden flag set for this bit?
                if ((bit_mask & run_state.outputs.overridden) == 0)
                {
                    // Skip to next bit if not overridden?
                    continue;
                }

                // This bit is currently overriden so use the override value
                if (bit_mask & run_state.outputs.override_value)
                {
                    // Overridden to on
                    outputs |= bit_mask;
                }
                else
                {
                    // Overridden to off
                    outputs &= ~bit_mask;
                }
            }

            pio_sm_put_blocking(shift_register_pio, shift_register_sm, outputs);
        }

        sleep_ms(5);
    }

    // Will never happen (because of core 1 forever loop), but here for completeness
    free(state);
}

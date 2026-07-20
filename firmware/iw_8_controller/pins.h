#ifndef __PINS_H__
#define __PINS_H__

// SPI 0
#define SPI0_CLK_PIN 2
#define SPI0_TX_PIN 3
#define SPI0_RX_PIN 4
#define SPI0_CS_PIN 5

// 74HC595
#define SHIFT_REG_DATA_PIN 10
#define SHIFT_REG_CLOCK_PIN 11
#define SHIFT_REG_LATCH_PIN 12
#define SHIFT_REG_OE_PIN 13

// UART 0
#define UART0_TX_PIN 0
#define UART0_RX_PIN 1
#define UART0_DE_PIN 6

#define UART1_TX_PIN 8
#define UART1_RX_PIN 9

// I2C 1
#define I2C1_DAT 18
#define I2C1_CLK 19

// ADC
#define ADC0_PIN 26
#define ADC1_PIN 27
#define ADC2_PIN 28

// INP 1
#define INP1_PIN 22

// INP 2
#define INP2_PIN 7

#define LED_PIN 25 // PICO_DEFAULT_LED_PIN

#endif // __PINS_H__
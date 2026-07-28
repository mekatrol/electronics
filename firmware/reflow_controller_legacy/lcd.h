#ifndef __LCD_H__
#define __LCD_H__

// LCD Pins
#define LCD_PINS_RS 16
#define LCD_PINS_ENABLE 17
#define LCD_PINS_D4 23
#define LCD_PINS_D5 25
#define LCD_PINS_D6 27
#define LCD_PINS_D7 29

// Encoder pins
#define BTN_EN1 31
#define BTN_EN2 33
#define BTN_ENC 35

// sd card Pins
#define CS 16
#define MOSI 17
#define SCK 23
#define SD_DETECT_PIN 49
#define SDSS 53

#define BEEPER_PIN 37
#define KILL_PIN 41

#define SCREEN_WIDTH 20
#define SCREEN_HEIGHT 4

void lcd_setup();
void lcd_loop();
void lcd_clear_line(int line);
void lcd_write_line(char *text, int line);
void lcd_continue_write_line(char *text);

#endif // __LCD_H__
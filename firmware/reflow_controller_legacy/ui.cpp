#include <Arduino.h>

#include "lcd.h"
#include "pins.h"
#include "plot.h"
#include "stage.h"
#include "ui.h"

char lcd_line_0[LINE_BUFFER_SIZE];
char lcd_line_1[LINE_BUFFER_SIZE];
char lcd_line_2[LINE_BUFFER_SIZE];
char lcd_line_3[LINE_BUFFER_SIZE];

char degc[3] = {
    (char)0xDF,
    'C',
    '\0'};

const char *DEGC = (const char *)degc;

void ui_blank_line(char *buffer)
{
    uint8_t len = 0;

    for (int i = 0; i < LINE_BUFFER_SIZE; i++)
    {
        // Reset to blank buffer
        buffer[i] = ' ';
    }

    // Null terminated
    buffer[LINE_BUFFER_SIZE - 1] = '\0';
}

void ui_append_line(char *buffer, char *text, bool clear_first)
{
    uint8_t len = 0;

    if (clear_first)
    {
        for (int i = 0; i < LINE_BUFFER_SIZE; i++)
        { // Reset to empty buffer
            buffer[i] = '\0';
        }
    }

    // Append text
    strcat(buffer, text);

    // Make sure always null terminated
    buffer[LINE_BUFFER_SIZE - 1] = '\0';
}

void ui_append_float(char *buffer, float f, bool clear_first)
{
    char text[LINE_BUFFER_SIZE];
    dtostrf(f, 3, 1, text);
    ui_append_line(buffer, text, clear_first);
}

void ui_append_int(char *buffer, float f, bool clear_first)
{
    char text[LINE_BUFFER_SIZE];
    dtostrf(f, 3, 0, text);
    ui_append_line(buffer, text, clear_first);
}

void ui_write_temps(float t1, float t2, float avg)
{
    ui_append_int(lcd_line_3, t1, true);
    ui_append_line(lcd_line_3, DEGC, false);
    ui_append_line(lcd_line_3, " ", false);
    ui_append_int(lcd_line_3, t2, false);
    ui_append_line(lcd_line_3, DEGC, false);
    ui_append_line(lcd_line_3, " ", false);
    ui_append_int(lcd_line_3, avg, false);
    ui_append_line(lcd_line_3, DEGC, false);
}

void ui_clear()
{
    for (int i = 0; i < 20; i++)
    {
        lcd_line_0[i] = ' ';
        lcd_line_1[i] = ' ';
        lcd_line_2[i] = ' ';
        lcd_line_3[i] = ' ';
    }

    lcd_line_0[20] = '\0';
    lcd_line_1[20] = '\0';
    lcd_line_2[20] = '\0';
    lcd_line_3[20] = '\0';
}

void ui_update(float t1, float t2, float t_avg, float setpoint, uint8_t flags, int8_t *val)
{
    plot_trend(setpoint, t1, t2, t_avg);

    uint8_t stage = stage_get_current_stage();

    ui_append_line(lcd_line_0, "Stage:    ", true);
    ui_append_line(lcd_line_0, stage_get_stage_name(stage), false);

    ui_append_line(lcd_line_1, "Setpoint: ", true);
    ui_append_float(lcd_line_1, setpoint, false);
    ui_append_line(lcd_line_1, DEGC, false);

    ui_blank_line(lcd_line_2);

    if (stage == STG_IDLE)
    {
        // Do nothing
    }
    else if (flags & UI_FLAG_DWELL)
    {
        lcd_line_2[0] = '-';
    }
    else
    {
        lcd_line_2[0] = '^';
    }

    if (flags & UI_FLAG_CYCLE)
    {
        lcd_line_2[1] = 'C';
    }

    if (val)
    {
        char text[LINE_BUFFER_SIZE];
        sprintf(text, "%d", *val);

        int i = 0;
        int len = strlen(text);
        while (i < len)
        {
            lcd_line_2[10 + i] = text[i];
            i++;
        }
    }

    ui_write_temps(t1, t2, t_avg);

    lcd_write_line(lcd_line_0, 0);
    lcd_write_line(lcd_line_1, 1);
    lcd_write_line(lcd_line_2, 2);
    lcd_write_line(lcd_line_3, 3);
}

void ui_init()
{
    lcd_setup();
    ui_clear();
    ui_update(0, 0, 0, 0, 0, NULL);
}

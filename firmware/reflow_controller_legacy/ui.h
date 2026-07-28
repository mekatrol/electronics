#ifndef __UI_H__
#define __UI_H__

#define LINE_BUFFER_SIZE 21

extern const char *DEGC;

#define UI_FLAG_DWELL 0x01
#define UI_FLAG_CYCLE 0x02

void ui_init();
void ui_clear();
void ui_update(float t1, float t2, float t_avg, float setpoint, uint8_t in_dwell, int8_t *val);
void ui_append_float(char *buffer, float f, bool clear_first);

#endif
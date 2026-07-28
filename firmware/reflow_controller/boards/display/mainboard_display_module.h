#ifndef REFLOW_CONTROLLER_MAINBOARD_DISPLAY_MODULE_H
#define REFLOW_CONTROLLER_MAINBOARD_DISPLAY_MODULE_H

/*
 * Interface for the Mini 12864 panel attached directly to the SKR mainboard.
 * The module has no MCU, startup code, linker script, scheduler, or separate
 * firmware image.
 */
void mainboard_display_module_initialize_hardware(void);

/* Run bounded LCD, encoder, and button service work. */
void mainboard_display_module_run_background_tasks(void);

/* Run bounded buzzer, RGB LED, or backlight feedback work. */
void mainboard_display_module_run_feedback_tasks(void);

#endif // REFLOW_CONTROLLER_MAINBOARD_DISPLAY_MODULE_H

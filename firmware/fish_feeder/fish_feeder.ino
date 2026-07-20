#include <Arduino.h>

#define X_STEP_PIN 54
#define X_DIR_PIN 55
#define X_ENABLE_PIN 38
#define X_MIN_PIN 3
#define X_MAX_PIN 2

#define Y_STEP_PIN 60
#define Y_DIR_PIN 61
#define Y_ENABLE_PIN 56
#define Y_MIN_PIN 14
#define Y_MAX_PIN 15

#define Z_STEP_PIN 46
#define Z_DIR_PIN 48
#define Z_ENABLE_PIN 62
#define Z_MIN_PIN 18
#define Z_MAX_PIN 19

#define E0_STEP_PIN 26
#define E0_DIR_PIN 28
#define E0_ENABLE_PIN 24

#define E1_STEP_PIN 36
#define E1_DIR_PIN 34
#define E1_ENABLE_PIN 30

#define STEP_DELAY 40 // 40 microseconds

#define LED_PIN 13
#define FAN_PIN 9

// Microstepping = 1/16, 16 steps for 1.8 degree [16]
// 1.8 Deg per step, 200 steps for 360 degree [200]
// 6 to 1 ratio between gears, 42 to 1 teeth [6]
// 16 * 200 * 6 = 19200
#define STEPS_PER_360_SMALL_GEAR 16 * 200                     // 3200
#define STEPS_PER_360_LARGE_GEAR STEPS_PER_360_SMALL_GEAR * 6 // 19200

#define STEPS_PER_DAY STEPS_PER_360_LARGE_GEAR / 8 // Approx 2400

#define INPUT_DEBOUNCE_COUNT 5

typedef struct input
{
    uint16_t pin;
    uint8_t state;
    uint8_t debounce_count;
} input_t;

input_t button;

void debounce(input_t *input, uint8_t input_state);
void nextFeed();

void debounce(input_t *input, uint8_t input_state)
{
    // Is the input state the same as the current input state?
    if (input_state == input->state)
    {
        // Reset debounce as they are the same value
        input->debounce_count = 0;
        return;
    }

    // Increment debounce count
    input->debounce_count++;

    // Reached the Debounce count threshold?
    if (input->debounce_count >= INPUT_DEBOUNCE_COUNT)
    {
        // Update the input state
        input->state = input_state;

        // Reset the count
        input->debounce_count = 0;
    }
}

void setup()
{
    pinMode(LED_PIN, OUTPUT);

    pinMode(X_STEP_PIN, OUTPUT);
    pinMode(X_DIR_PIN, OUTPUT);
    pinMode(X_ENABLE_PIN, OUTPUT);
    pinMode(X_MIN_PIN, INPUT_PULLUP);

    pinMode(Y_STEP_PIN, OUTPUT);
    pinMode(Y_DIR_PIN, OUTPUT);
    pinMode(Y_ENABLE_PIN, OUTPUT);

    pinMode(Z_STEP_PIN, OUTPUT);
    pinMode(Z_DIR_PIN, OUTPUT);
    pinMode(Z_ENABLE_PIN, OUTPUT);

    pinMode(E0_STEP_PIN, OUTPUT);
    pinMode(E0_DIR_PIN, OUTPUT);
    pinMode(E0_ENABLE_PIN, OUTPUT);

    pinMode(E1_STEP_PIN, OUTPUT);
    pinMode(E1_DIR_PIN, OUTPUT);
    pinMode(E1_ENABLE_PIN, OUTPUT);

    digitalWrite(X_ENABLE_PIN, HIGH);
    digitalWrite(Y_ENABLE_PIN, HIGH);
    digitalWrite(Z_ENABLE_PIN, HIGH);
    digitalWrite(E0_ENABLE_PIN, HIGH);
    digitalWrite(E1_ENABLE_PIN, HIGH);
}

uint32_t last_tick = 0;
uint8_t fan_state = 0;
void loop()
{
    uint32_t tick = millis();

    // Only execute the loop every 2 ms (this also sets the input debounce rate)
    if (tick - last_tick < 2)
    {
        return;
    }

    last_tick = tick;

    // Remember the current button state
    uint8_t prev_button_state = button.state;

    // Read the current button input state
    uint8_t current_button_state = digitalRead(X_MIN_PIN) == LOW ? HIGH : LOW; // RAMPS 1.4 End stops are inverted

    // Debound the button
    debounce(&button, current_button_state);

    // Has the state changed?
    if (prev_button_state != button.state && button.state == HIGH)
    {
        nextFeed();
    }
}

void move(uint16_t enable_pin, uint16_t direction_pin, uint8_t direction, uint16_t step_pin, uint16_t steps)
{
    digitalWrite(direction_pin, direction);
    digitalWrite(enable_pin, LOW);

    for (int i = 0; i < steps; i++)
    {
        digitalWrite(step_pin, HIGH);
        delayMicroseconds(STEP_DELAY);
        digitalWrite(step_pin, LOW);
        delayMicroseconds(STEP_DELAY);
    }

    digitalWrite(enable_pin, HIGH);
}

void shake(uint16_t enable_pin, uint16_t direction_pin, uint16_t step_pin)
{
    for (int i = 0; i < 20; i++)
    {
        move(enable_pin, direction_pin, HIGH, step_pin, 400);
        delayMicroseconds(100);
        move(enable_pin, direction_pin, LOW, step_pin, 400);
        delayMicroseconds(100);
    }
}

void moveAndShake(uint16_t enable_pin, uint16_t direction_pin, uint8_t move_direction, uint16_t step_pin, uint16_t steps)
{
    move(enable_pin, direction_pin, direction_pin, step_pin, steps);
    shake(enable_pin, direction_pin, step_pin);
}

void nextFeed()
{
    moveAndShake(E0_ENABLE_PIN, E0_DIR_PIN, LOW, E0_STEP_PIN, STEPS_PER_DAY);
    moveAndShake(E1_ENABLE_PIN, E1_DIR_PIN, LOW, E1_STEP_PIN, STEPS_PER_DAY);
}

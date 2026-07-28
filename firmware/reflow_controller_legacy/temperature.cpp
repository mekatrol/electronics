#include "pins.h"
#include "temperature.h"

// Adapted from Marin firmware
// R25 = 100 kOhm, beta25 = 4092 K, 4.7 kOhm pull-up, bed thermistor
constexpr temp_entry_t temp_adc_to_celsius_table[] PROGMEM = {
    {23, 300},
    {25, 295},
    {27, 290},
    {28, 285},
    {31, 280},
    {33, 275},
    {35, 270},
    {38, 265},
    {41, 260},
    {44, 255},
    {48, 250},
    {52, 245},
    {56, 240},
    {61, 235},
    {66, 230},
    {71, 225},
    {78, 220},
    {84, 215},
    {92, 210},
    {100, 205},
    {109, 200},
    {120, 195},
    {131, 190},
    {143, 185},
    {156, 180},
    {171, 175},
    {187, 170},
    {205, 165},
    {224, 160},
    {245, 155},
    {268, 150},
    {293, 145},
    {320, 140},
    {348, 135},
    {379, 130},
    {411, 125},
    {445, 120},
    {480, 115},
    {516, 110},
    {553, 105},
    {591, 100},
    {628, 95},
    {665, 90},
    {702, 85},
    {737, 80},
    {770, 75},
    {801, 70},
    {830, 65},
    {857, 60},
    {881, 55},
    {903, 50},
    {922, 45},
    {939, 40},
    {954, 35},
    {966, 30},
    {977, 25},
    {985, 20},
    {993, 15},
    {999, 10},
    {1004, 5},
    {1008, 0},
    {1012, -5},
    {1016, -10},
    {1020, -15}};

#define ADC_TO_CELSIUS_TBL_LEN sizeof(temp_adc_to_celsius_table) / sizeof(temp_entry_t)

float temp_analog_to_celsius(const uint16_t raw)
{
    do
    {
        // Set to array start (0th element)
        uint8_t left = 0;

        // Set to array end (count element)
        uint8_t right = ADC_TO_CELSIUS_TBL_LEN;

        uint8_t middle;

        // Iterate until we find value to interpolate
        for (;;)
        {
            // Split left and right in half (average values)
            middle = (left + right) >> 1;

            // Is middle now first element?
            if (!middle)
            {
                // Just return the first entry celsius value
                return int16_t(pgm_read_word(&temp_adc_to_celsius_table[0].celsius));
            }

            // Have we scanned all values?
            if (middle == left || middle == right)
            {
                // Just return last entry in table
                return int16_t(pgm_read_word(&temp_adc_to_celsius_table[ADC_TO_CELSIUS_TBL_LEN - 1].celsius));
            }

            // Get values about middle
            uint16_t v00 = pgm_read_word(&temp_adc_to_celsius_table[middle - 1].value),
                     v10 = pgm_read_word(&temp_adc_to_celsius_table[middle - 0].value);

            // If raw is less than first middle value then set right to middle as new end
            if (raw < v00)
            {
                right = middle;
            }

            // If raw is more than second middle value then set left to middle as new start
            else if (raw > v10)
            {
                left = middle;
            }

            // We are in rangle of left and right
            else
            {
                const int16_t v01 = int16_t(pgm_read_word(&temp_adc_to_celsius_table[middle - 1].celsius)),
                              v11 = int16_t(pgm_read_word(&temp_adc_to_celsius_table[middle - 0].celsius));

                // Interpolate between two values
                return v01 + (raw - v00) * float(v11 - v01) / float(v10 - v00);
            }
        }
    } while (0);
}
#include <SPI.h>
#include <SD.h>
#include <LiquidCrystal.h>

///
/// https://github.com/ellensp/rrd-lcd-tester
///

#include "lcd.h"

LiquidCrystal lcd(LCD_PINS_RS, LCD_PINS_ENABLE, LCD_PINS_D4, LCD_PINS_D5, LCD_PINS_D6, LCD_PINS_D7); // RS,Enable,D4,D5,D6,D7

int encoderPos = 8;     // Current encoder position, mid way on scale
int encoderPosLast = 8; // Last encoder position, midway on scale
int encoder0PinALast;   // Used to decode rotory encoder, last value
int encoder0PinNow;     // Used to decode rotory encoder, current value

Sd2Card card;
SdVolume volume;

int sdcardinit;
int sdcardtype;
int sdvolumeinit;
int sdvolumefattype;
uint32_t sdvolumebpc;
uint32_t sdvolumecc;
char tmp_string[16];

// Customer characters for corner of logo
byte customChar0[] = {
    B00000, B00000, B00000, B00111, B00100, B00100, B00100, B00100};
byte customChar1[] = {
    B00000, B00000, B00000, B11100, B00100, B00100, B00100, B00100};
byte customChar2[] = {
    B00100, B00100, B00100, B00111, B00000, B00000, B00000, B00000};
byte customChar3[] = {
    B00100, B00100, B00100, B11100, B00000, B00000, B00000, B00000};

static void lcd_startup_display()
{
    lcd.setCursor(0, 0);
    lcd.print('\x00');
    lcd.print("------------------");
    lcd.write('\x01');
    lcd.setCursor(0, 1);
    lcd.print("| Reflow Control   |");
    lcd.setCursor(0, 2);
    lcd.write('\x02');
    lcd.print("------------------");
    lcd.write('\x03');
}

static void lcd_clear_line(int line)
{
    lcd.setCursor(0, line);
    lcd.print("                    ");
}

static void lcd_write_line(char *text, int line)
{
    lcd_clear_line(line);
    lcd.setCursor(0, line);
    lcd.print(text);
}

static void lcd_continue_write_line(char *text)
{
    lcd.print(text);
}

static void lcd_status_line(char *text)
{
    lcd_clear_line(3);
    lcd.setCursor(0, 3);
    lcd.print(text);
}

static void encoder_status_line(int value)
{
    // Serial.println(value);
    lcd.setCursor(0, 3);
    lcd.print("Enc:                ");
    lcd.setCursor(4, 3);
    for (int x = 0; x < value; x++)
    {
        lcd.print("*");
    }
}

static void sdcardinfo()
{
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Initializing SD card");
    if (sdcardinit)
    {
        lcd.setCursor(0, 1);
        lcd.print("Card type:");
        switch (sdcardtype)
        {
        case SD_CARD_TYPE_SD1:
            lcd.setCursor(11, 1);
            lcd.print("SD1");
            break;
        case SD_CARD_TYPE_SD2:
            lcd.setCursor(11, 1);
            lcd.print("SD2");
            break;
        case SD_CARD_TYPE_SDHC:
            lcd.setCursor(11, 1);
            lcd.print("SDHC");
            break;
        default:
            lcd.setCursor(11, 1);
            lcd.print("Unknown");
        }

        if (!sdvolumeinit)
        {
            lcd.setCursor(0, 2);
            lcd.print("No FAT16/FAT32");
        }
        else
        {
            // print the type and size of the first FAT-type volume
            lcd.setCursor(0, 2);
            lcd.print("Volume type: FAT");
            itoa(sdvolumefattype, tmp_string, 10);
            lcd.print(tmp_string);

            uint32_t volumesize;
            volumesize = sdvolumebpc; // clusters are collections of blocks
            volumesize *= sdvolumecc; // we'll have a lot of clusters
            volumesize /= 2;          // SD card blocks are always 512 bytes (2 blocks are 1KB)
            volumesize /= 1024;

            lcd.setCursor(0, 3);
            lcd.print("Volume size(Mb):");
            itoa(volumesize, tmp_string, 10);
            lcd.print(tmp_string);
        }
    }
    else
    {
        lcd.setCursor(0, 1);
        lcd.print("FAILED");
    }
}

void lcd_setup()
{
    lcd.begin(SCREEN_WIDTH, SCREEN_WIDTH);

    // Print a message to the LCD.
    lcd.createChar(0, customChar0);
    lcd.createChar(1, customChar1);
    lcd.createChar(2, customChar2);
    lcd.createChar(3, customChar3);

    pinMode(SD_DETECT_PIN, INPUT);     // Set SD_DETECT_PIN as an unput
    digitalWrite(SD_DETECT_PIN, HIGH); // turn on pullup resistors
    pinMode(KILL_PIN, INPUT);          // Set KILL_PIN as an unput
    digitalWrite(KILL_PIN, HIGH);      // turn on pullup resistors
    pinMode(BTN_EN1, INPUT);           // Set BTN_EN1 as an unput, half of the encoder
    digitalWrite(BTN_EN1, HIGH);       // turn on pullup resistors
    pinMode(BTN_EN2, INPUT);           // Set BTN_EN2 as an unput, second half of the encoder
    digitalWrite(BTN_EN2, HIGH);       // turn on pullup resistors
    pinMode(BTN_ENC, INPUT);           // Set BTN_ENC as an unput, encoder button
    digitalWrite(BTN_ENC, HIGH);       // turn on pullup resistors
    pinMode(BEEPER_PIN, OUTPUT);       // Set BTN_ENC as an unput, encoder button

    // dependion on power on position of encoder adjust encoderPosLast
    if (digitalRead(BTN_EN1) && digitalRead(BTN_EN2))
    {
        encoderPosLast--;
    }
    else if ((!digitalRead(BTN_EN1) && digitalRead(BTN_EN2)) || (digitalRead(BTN_EN1) && !digitalRead(BTN_EN2)))
    {
        encoderPosLast++;
    }

    lcd_startup_display();
    lcd_status_line("Initialising...");
}

void lcd_sd_card_detected()
{
    lcd_status_line("SD Card Inserted");
    sdcardinit = card.init(SPI_HALF_SPEED, SDSS);
    if (!sdcardinit)
    {
        sdcardinit = card.init(SPI_HALF_SPEED, SDSS); // try it again.
    }

    sdcardtype = card.type();
    sdvolumeinit = volume.init(card);
    sdvolumefattype = volume.fatType();
    sdvolumebpc = volume.blocksPerCluster();
    sdvolumecc = volume.clusterCount();
    sdcardinfo();

    while (!digitalRead(SD_DETECT_PIN))
        ; // wait for sd card to be removed.

    lcd.clear();

    lcd_startup_display();
    lcd_status_line("SD Card Removed");
}

void lcd_loop()
{
    // If sd card is inserted display SD card info
    if (!digitalRead(SD_DETECT_PIN))
    {
        lcd_sd_card_detected();
    }
    else
    {
        // Read the encoder and update encoderPos
        encoder0PinNow = digitalRead(BTN_EN2);
        if ((encoder0PinALast == LOW) && (encoder0PinNow == HIGH))
        {
            if (digitalRead(BTN_EN1) == LOW)
            {
                encoderPos++;
                if (encoderPos > SCREEN_WIDTH - 4)
                {
                    encoderPos = SCREEN_WIDTH - 4;
                }
            }
            else
            {
                encoderPos--;
                if (encoderPos < 0)
                {
                    encoderPos = 0;
                }
            }
        }
        encoder0PinALast = encoder0PinNow;
        if (encoderPos != encoderPosLast)
        {
            encoder_status_line(encoderPos);
        }
        encoderPosLast = encoderPos;

        // check if both buttons and sound the ebuzzer
        if (!digitalRead(BTN_ENC) && !digitalRead(KILL_PIN))
        {
            lcd_status_line("Buzzer activated");
            digitalWrite(BEEPER_PIN, HIGH);
            while (!digitalRead(BTN_ENC) && !digitalRead(KILL_PIN))
            {
                ; // wait for button release
            }
            digitalWrite(BEEPER_PIN, LOW);
            lcd_status_line("Buzzer deactivated");
        }

        // check encoder button
        if (!digitalRead(BTN_ENC) && digitalRead(KILL_PIN))
        {
            lcd_status_line("Enc: button pressed");
            // digitalWrite(BEEPER_PIN, HIGH);
            while (!digitalRead(BTN_ENC) && digitalRead(KILL_PIN))
                ;
            // digitalWrite(BEEPER_PIN, LOW);
            lcd_status_line("Enc: button released");
        }

        // Check Kill Pin
        if (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
        {
            lcd_status_line("Kill button pressed");
            while (!digitalRead(KILL_PIN) && digitalRead(BTN_ENC))
            {
                ;
            }
            lcd_status_line("Kill button released");
        }
    }
}
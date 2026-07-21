import RPi.GPIO as GPIO
import time

shift_sleep = 5E-6

# Shift In - 74HC165
shift_in_data = 17              #  9 The serial data output QH (input to CPU)
shift_in_load = 11              #  1 Sift or Load flag 0 = load from parallel, 1 = load from serial (PL)
shift_in_clock = 9              #  2 Clock data through shift register (CP)
shift_in_clock_enable = 8       # 15 Set low to enable clocking, high to inhibit clocking (CE)
shift_in_serial_data = 10       # 10 Serial input (DS)

# Shift out - 74HC565

pb_1 = 7
shutdown = 21

status_led_1 = 19
status_led_2 = 16
status_led_3 = 20
status_led_4 = 26

# Set GPIO mode to use logical pin numbering
GPIO.setmode(GPIO.BCM)

# Disable warning, eg 'Pin already in use, assigned, etc)
GPIO.setwarnings(False)

# Init Shift In (74HC165)
GPIO.setup(shift_in_data, GPIO.IN)
GPIO.setup(shift_in_load, GPIO.OUT)
GPIO.setup(shift_in_clock, GPIO.OUT)
GPIO.setup(shift_in_clock_enable, GPIO.OUT)
GPIO.setup(shift_in_serial_data, GPIO.OUT)

# Load parallel inputs
GPIO.output(shift_in_load, GPIO.LOW)

# Disable clock
GPIO.output(shift_in_clock_enable, GPIO.LOW)

# Set clock low
GPIO.output(shift_in_clock, GPIO.LOW)

# Set serial data low (not used in this test)
GPIO.output(shift_in_serial_data, GPIO.LOW)

# Init Shift Out (74HC565)
shift_out_data = 4 # 14
shift_out_clock = 22 # 11
shift_out_latch = 27 # 12
shift_out_enable = 18 # 13

GPIO.setup(shift_out_data, GPIO.OUT)
GPIO.setup(shift_out_clock, GPIO.OUT)
GPIO.setup(shift_out_latch, GPIO.OUT)
GPIO.setup(shift_out_enable, GPIO.OUT)

GPIO.output(shift_out_data, GPIO.LOW)
GPIO.output(shift_out_clock, GPIO.LOW)
GPIO.output(shift_out_latch, GPIO.LOW)
GPIO.output(shift_out_enable, GPIO.HIGH)

GPIO.setup(pb_1,GPIO.IN)
GPIO.setup(shutdown,GPIO.IN)

GPIO.setup(status_led_1,GPIO.OUT)
GPIO.setup(status_led_2,GPIO.OUT)
GPIO.setup(status_led_3,GPIO.OUT)
GPIO.setup(status_led_4,GPIO.OUT)

GPIO.output(status_led_1, GPIO.HIGH)
GPIO.output(status_led_2, GPIO.HIGH)
GPIO.output(status_led_3, GPIO.HIGH)
GPIO.output(status_led_4, GPIO.HIGH)

def shift_in():
    # Enable clocking
    #GPIO.output(shift_in_clock_enable, GPIO.LOW)

    # Latch parallel data into shift register
    GPIO.output(shift_in_load, GPIO.LOW)
    time.sleep(shift_sleep)
    GPIO.output(shift_in_load, GPIO.HIGH)

    val = 0
    for bit_number in range(8): 
        # Sample bit value
        input_value = GPIO.input(shift_in_data)
        print("input_value: " + format(input_value, 'b'))

        # Clock input value
        GPIO.output(shift_in_clock, GPIO.HIGH)

        # Let settle
        time.sleep(shift_sleep)

        # Set clock low again
        GPIO.output(shift_in_clock, GPIO.LOW)

        # Move bit to correct position
        val = val | input_value << (7 - bit_number)

    # Disable clocking
    #GPIO.output(shift_in_clock_enable, GPIO.LOW)

    return val

def shift_out(data):
    GPIO.output(shift_out_latch, GPIO.LOW)

    for i in range(8):
        bit = (0x80 >> i) & data
        
        GPIO.output(shift_out_data, bit)
        GPIO.output(shift_out_clock, GPIO.HIGH)
        time.sleep(shift_sleep)
        GPIO.output(shift_out_clock, GPIO.LOW)

    GPIO.output(shift_out_latch, GPIO.HIGH)
    GPIO.output(shift_out_enable, GPIO.LOW)

    return

while True:
    # If button is pushed, light up LED
    try:
        while True:
            inputs = shift_in()
            shift_out(inputs)

            pb_1_val = GPIO.input(pb_1)

            if pb_1_val:
                GPIO.output(status_led_1, GPIO.LOW)
                GPIO.output(status_led_3, GPIO.LOW)
            else:
                GPIO.output(status_led_1, GPIO.HIGH)
                GPIO.output(status_led_3, GPIO.HIGH)

            shutdown_val = GPIO.input(shutdown)

            if shutdown_val:
                GPIO.output(status_led_2, GPIO.LOW)
                GPIO.output(status_led_4, GPIO.LOW)
            else:
                GPIO.output(status_led_2, GPIO.HIGH)
                GPIO.output(status_led_4, GPIO.HIGH)

            time.sleep(0.05)

    # When you press ctrl+c, this will be called
    finally:
        GPIO.cleanup()

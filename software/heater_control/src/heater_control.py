import RPi.GPIO as GPIO
import glob
import os
import time
from datetime import datetime

shift_sleep = 5e-6

# Shift In - 74HC165
shift_in_data = 17  #  9 The serial data output QH (input to CPU)
shift_in_load = (
    11  #  1 Sift or Load flag 0 = load from parallel, 1 = load from serial (PL)
)
shift_in_clock = 9  #  2 Clock data through shift register (CP)
shift_in_clock_enable = (
    8  # 15 Set low to enable clocking, high to inhibit clocking (CE)
)
shift_in_serial_data = 10  # 10 Serial input (DS)

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
shift_out_data = 4  # 14
shift_out_clock = 22  # 11
shift_out_latch = 27  # 12
shift_out_enable = 18  # 13

GPIO.setup(shift_out_data, GPIO.OUT)
GPIO.setup(shift_out_clock, GPIO.OUT)
GPIO.setup(shift_out_latch, GPIO.OUT)
GPIO.setup(shift_out_enable, GPIO.OUT)

GPIO.output(shift_out_data, GPIO.LOW)
GPIO.output(shift_out_clock, GPIO.LOW)
GPIO.output(shift_out_latch, GPIO.LOW)
GPIO.output(shift_out_enable, GPIO.HIGH)

GPIO.setup(pb_1, GPIO.IN)
GPIO.setup(shutdown, GPIO.IN)

GPIO.setup(status_led_1, GPIO.OUT)
GPIO.setup(status_led_2, GPIO.OUT)
GPIO.setup(status_led_3, GPIO.OUT)
GPIO.setup(status_led_4, GPIO.OUT)

GPIO.output(status_led_1, GPIO.HIGH)
GPIO.output(status_led_2, GPIO.HIGH)
GPIO.output(status_led_3, GPIO.HIGH)
GPIO.output(status_led_4, GPIO.HIGH)


# Enable 1 wire bus on GPIO 2
# nano /boot/config.txt
# [all]
# dtoverlay=w1-gpio,gpiopin=2

os.system("modprobe w1-gpio")
os.system("modprobe w1-therm")

base_dir = "/sys/bus/w1/devices/"
device_folder1 = glob.glob(base_dir + "28*")[0]
device_file1 = device_folder1 + "/w1_slave"
device_folder2 = glob.glob(base_dir + "28*")[1]
device_file2 = device_folder2 + "/w1_slave"


def read_temp_raw1():
    f = open(device_file1, "r")
    lines = f.readlines()
    f.close()
    return lines


def read_temp_raw2():
    f = open(device_file2, "r")
    lines = f.readlines()
    f.close()
    return lines


def read_temp1():
    lines = read_temp_raw1()
    while lines[0].strip()[-3:] != "YES":
        time.sleep(0.2)
        lines = read_temp_raw1()
    equals_pos = lines[1].find("t=")
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2 :]
        temp_c = float(temp_string) / 1000.0
        return temp_c


def read_temp2():
    lines = read_temp_raw2()
    while lines[0].strip()[-3:] != "YES":
        time.sleep(0.2)
        lines = read_temp_raw2()
    equals_pos = lines[1].find("t=")
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2 :]
        temp_c = float(temp_string) / 1000.0
        return temp_c


def shift_in():
    # Latch parallel data into shift register
    GPIO.output(shift_in_load, GPIO.LOW)
    time.sleep(shift_sleep)
    GPIO.output(shift_in_load, GPIO.HIGH)

    val = 0
    for bit_number in range(8):
        # Sample bit value
        input_value = GPIO.input(shift_in_data)
        print("input_value: " + format(input_value, "b"))

        # Clock input value
        GPIO.output(shift_in_clock, GPIO.HIGH)

        # Let settle
        time.sleep(shift_sleep)

        # Set clock low again
        GPIO.output(shift_in_clock, GPIO.LOW)

        # Move bit to correct position
        val = val | input_value << (7 - bit_number)

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
    heater_on = 0
    temp_set = 21.5
    temp_pb = 1.0

    # If button is pushed, light up LED
    try:
        while True:
            with open("/home/pi/src/temp.settings") as f:
                temp_set, temp_pb = [float(x) for x in next(f).split()]

            temp_1 = read_temp1()
            temp_2 = read_temp2()
            avg_temp = (temp_1 + temp_2) / 2
            current_date_time = datetime.now()

            day_time = current_date_time.hour >= 8 and current_date_time.hour < 17

            # inputs = shift_in()
            if day_time:
                temp_set = 15  # Lower temp during the day

            if avg_temp < temp_set:
                heater_on = 1
            elif avg_temp >= (temp_set + temp_pb):
                heater_on = 0

            with open("/home/pi/src/temp.log", "a") as f:
                f.write(
                    current_date_time.strftime("%Y-%m-%d %H:%M:%S")
                    + ","
                    + format(temp_1)
                    + ","
                    + format(temp_2)
                    + ","
                    + format(avg_temp)
                    + ","
                    + format(temp_set)
                    + ","
                    + format(temp_pb)
                    + ","
                    + ("on" if heater_on else "off")
                    + ","
                    + ("yes" if day_time else "no")
                    + "\n"
                )

            shift_out(heater_on)

            GPIO.output(status_led_1, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(status_led_1, GPIO.LOW)

            pb_1_val = GPIO.input(pb_1)

            if pb_1_val:
                GPIO.output(status_led_3, GPIO.LOW)
            else:
                GPIO.output(status_led_3, GPIO.HIGH)

            shutdown_val = GPIO.input(shutdown)

            if shutdown_val:
                GPIO.output(status_led_2, GPIO.LOW)
                GPIO.output(status_led_4, GPIO.LOW)
            else:
                GPIO.output(status_led_2, GPIO.HIGH)
                GPIO.output(status_led_4, GPIO.HIGH)

            time.sleep(59)

    # When you press ctrl+c, this will be called
    finally:
        GPIO.cleanup()

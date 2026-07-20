# This example shows you a simple, non-interrupt way of reading Pico Display's buttons with a loop that checks to see if buttons are pressed.

import time
from pimoroni import RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4
import network
import socket
import struct
import select
from time import gmtime
from machine import Pin, disable_irq, enable_irq

from config import *

BUTTON_DEBOUNCE_COUNT = 10
DISPLAY_ON_COUNT_TICKS = 10000

# Runtime state
refreshed_date_time = False
ntp_dow = -1
fed_fish = True
display_on = True
display_on_count = DISPLAY_ON_COUNT_TICKS

# Stepper motor pins
stepper1_enable_pin = Pin(0, Pin.OUT)
stepper1_step_pin = Pin(1)
stepper1_direction_pin = Pin(2, Pin.OUT)
stepper1_enable_pin.value(1)
stepper1_direction_pin.value(0)

stepper2_enable_pin = Pin(3, Pin.OUT)
stepper2_step_pin = Pin(4)
stepper2_direction_pin = Pin(5, Pin.OUT)
stepper2_enable_pin.value(1)
stepper2_direction_pin.value(0)

# Flags to signal that the state machine is busy stepping
state_machine_busy_flags = [0, 0]

# Get real time clock
rtc = machine.RTC()

# Init display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4, rotate=0)
display.set_backlight(0.5)
display.set_font("bitmap8")

# Create colour palette
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
CYAN = display.create_pen(0, 255, 255)
MAGENTA = display.create_pen(255, 0, 255)
YELLOW = display.create_pen(255, 255, 0)
GREEN = display.create_pen(0, 255, 0)

# Lines to display on screen
line1 = ""
line2 = ""
line3 = ""
line4 = ""
line5 = ""
line6 = ""
line7 = ""
line8 = ""

line_height_in_pixels = 30

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
# (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600 if gmtime(0)[0] == 2000 else 2208988800

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
ntp_host = config["time_server"]

# WLAN connected status flag
is_wlan_connected = False


@rp2.asm_pio(
    set_init=(rp2.PIO.OUT_HIGH),
    sideset_init=(rp2.PIO.OUT_LOW),
)
def do_steps():
    wrap_target()  # Main loop here
    pull().side(0x00)[0]  # Block until data pulled from OSR, side bits low
    mov(x, osr)  # OSR is loaded with the number of steps
    label("steps_loop")  # Loop here for number of steps
    set(pins, 0)[
        1
    ]  # Enable stepper driver (stepper1_enable_pin bit set low to stepper1_enable_pin) [One cycle delay after]
    nop().side(0x01)  # Set stepper1_step_pin bit
    nop()[3]  # 3 cycles delay
    nop()[3]  # 3 cycles delay
    nop().side(0x00)  # Clear stepper1_step_pin bit
    nop()[3]  # 3 cycles delay
    nop()[3]  # 3 cycles delay
    jmp(x_dec, "steps_loop")  # Loop until number of steps complete
    nop()[3]  # 3 cycles delay
    set(pins, 1)[
        1
    ]  # Disable stepper driver (stepper1_enable_pin bit set high to disable) [One cycle delay after]
    irq(noblock, rel(0))  # Raise IRQ to flag steps finished
    wrap()


def is_sm_busy(sm):
    irq_state = disable_irq()  # Start of critical section
    sm_busy = state_machine_busy_flags[sm] == 1
    enable_irq(irq_state)  # End of critical section
    return sm_busy


def sm0_irq_handler(sm):
    # Clear busy flag
    state_machine_busy_flags[0] = 0


def sm1_irq_handler(sm):
    # Clear busy flag
    state_machine_busy_flags[1] = 0


stepper1 = rp2.StateMachine(
    0,
    do_steps,
    freq=200000,
    set_base=stepper1_enable_pin,
    sideset_base=stepper1_step_pin,
)
stepper1.irq(sm0_irq_handler)
stepper1.active(1)


stepper2 = rp2.StateMachine(
    1,
    do_steps,
    freq=200000,
    set_base=stepper2_enable_pin,
    sideset_base=stepper2_step_pin,
)
stepper2.irq(sm1_irq_handler)
stepper2.active(1)


def move(sm_num, step_direction, step_count):
    # Wait till state machine is not busy
    while is_sm_busy(sm_num):
        update_display()
        time.sleep(0.05)

    state_machine_busy_flags[sm_num] = 1

    if sm_num == 0:
        stepper1_direction_pin.value(step_direction)
        stepper1.put(step_count)
    elif sm_num == 1:
        stepper2_direction_pin.value(step_direction)
        stepper2.put(step_count)


def shake(sm_num):
    shakes = 20
    while shakes >= 0:
        shakes -= 1
        move(sm_num, 0, 400)
        move(sm_num, 1, 400)


def move_and_shake(sm_num):
    global line4

    line4 = "Feed %d Move" % (sm_num + 1)
    move(sm_num, 1, 2400)

    line4 = "Feed %d Pause" % (sm_num + 1)

    ticks = 10
    while ticks > 0:
        ticks -= 1
        update_display()
        time.sleep(0.1)

    line4 = "Feed %d Shake" % (sm_num + 1)
    shake(sm_num)

    line4 = ""


def ts_time(hrs_offset=0):  # Local time offset in hrs relative to UTC
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    try:
        addr = socket.getaddrinfo(ntp_host, 123)[0][-1]
    except OSError:
        return 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    poller = select.poll()
    poller.register(s, select.POLLIN)
    try:
        s.sendto(NTP_QUERY, addr)
        if poller.poll(1000):  # time in milliseconds
            msg = s.recv(48)
            val = struct.unpack("!I", msg[40:44])[0]  # Can return 0
            return max(val - NTP_DELTA + hrs_offset * 3600, 0)
    except OSError:
        pass  # LAN error
    finally:
        s.close()
    return 0  # Timeout or LAN error occurred


# Clear screen
def clear():
    display.set_pen(BLACK)
    display.clear()
    display.update()


def update_display():
    global display_on

    display.set_pen(BLACK)
    display.clear()

    if not display_on:
        return

    timestamp = rtc.datetime()
    line1 = "%02d/%02d %02d:%02d:%02d" % (
        timestamp[2:3] + timestamp[1:2] + timestamp[4:7]
    )

    line2 = "NTP: %d FED: %d" % (refreshed_date_time, fed_fish)

    display.set_pen(YELLOW)

    display.text(line1, 5, line_height_in_pixels * 0, 320, 4)

    display.set_pen(MAGENTA)

    display.text(line2, 5, line_height_in_pixels * 1, 320, 4)

    display.text(line3, 5, line_height_in_pixels * 2, 320, 4)

    display.set_pen(CYAN)

    display.text(line4, 5, line_height_in_pixels * 3, 320, 4)

    display.set_pen(WHITE)

    display.text(line5, 5, line_height_in_pixels * 4, 320, 4)

    display.text(line6, 5, line_height_in_pixels * 5, 320, 4)

    display.set_pen(GREEN)
    display.text(line7, 5, line_height_in_pixels * 6, 320, 4)

    display.set_pen(WHITE)
    display.text(line8, 5, line_height_in_pixels * 7, 320, 4)
    display.update()


def wlan_connect(ssid, pwd):
    global line3

    wlan.disconnect()
    wlan.connect(ssid, pwd)

    # Wait for connect or fail
    wait = 30
    while wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        wait -= 1
        line3 = "Wait: %d" % (wait)
        update_display()
        time.sleep(1)
    line3 = ""


def wlan_connected():
    return wlan.status() == 3


def wlan_init():
    global line7
    global line8
    global is_wlan_connected

    led.red(0.1)

    # Get preferred WAN SSID and password from config file
    wlan_ssid = config["wlan_ssid"]
    wlan_pwd = config["wlan_pwd"]
    line7 = "*" + wlan_ssid
    line8 = "000.000.000.000"

    # Connect to WLAN
    wlan_connect(wlan_ssid, wlan_pwd)

    # If WLAN did not connect then try fallback SSID and password
    if not wlan_connected():
        wlan_ssid = config["wlan_ssid_fallback"]
        wlan_pwd = config["wlan_pwd_fallback"]
        line7 = "*" + wlan_ssid
        wlan_connect(wlan_ssid, wlan_pwd)

    # Handle connection error
    if not wlan_connected():
        line8 = "000.000.000.000"
    else:
        line8 = wlan.ifconfig()[0]
        is_wlan_connected = True

        # Display the SSID that we actually connected to
        line7 = wlan_ssid

    led.green(0.1)


def refresh_date_time():
    global led

    if not is_wlan_connected:
        return  # Can't refresh date / time if WLAN not connected

    led.red(0.1)

    # gmtime returns time.struct_time
    # 0 tm_year (for example, 1993)
    # 1 tm_mon  range [1, 12]
    # 2 tm_mday range [1, 31]
    # 3 tm_hour range [0, 23]
    # 4 tm_min  range [0, 59]
    # 5 tm_sec  range [0, 61]
    # 6 tm_wday range [0, 6], Monday is 0
    # 7 tm_yday range [1, 366]
    # 8 tm_isdst    0, 1 or -1

    dt = gmtime(ts_time(11))

    # rtc.datetime takes tuple (year, month, day, weekday, hours, minutes, seconds, subseconds)
    rtc.datetime((dt[0], dt[1], dt[2], dt[7], dt[3], dt[4], dt[5], dt[6]))

    led.green(0.1)


def feed_fish():
    global fed_fish

    led.blue(0.5)
    move_and_shake(0)
    move_and_shake(1)
    led.green(0.1)
    fed_fish = True


def turn_on_display():
    global display_on
    global display_on_count
    global led

    display_on = True
    display_on_count = DISPLAY_ON_COUNT_TICKS
    display.set_backlight(0.5)
    led.green(0.1)


def turn_off_display():
    global display_on
    global display_on_count
    global led

    display_on = False
    display_on_count = 0
    display.set_backlight(0.0)
    led.off()


class RGBLed:
    def __init__(self):
        self.led = RGBLED(6, 7, 8)
        self.led.set_rgb(0, 0, 0)

    def off(self):
        self.led.set_rgb(0, 0, 0)

    def red(self, intensity=0.5):
        self.led.set_rgb(255 * intensity, 0, 0)

    def green(self, intensity=0.5):
        self.led.set_rgb(0, 255 * intensity, 0)

    def blue(self, intensity=0.5):
        self.led.set_rgb(0, 0, 255 * intensity)


class ButtonDebounce:
    def __init__(self, pin):
        self.state = False
        self.debounce_count = 0
        self.pin_number = pin
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)

    def read(self):
        return not self.pin.value()

    def debounce(self):
        global display_on

        changed = False

        newState = self.read()

        if newState != self.state:
            self.debounce_count += 1
            if self.debounce_count >= BUTTON_DEBOUNCE_COUNT:
                self.state = newState
                self.debounce_count = 0
                changed = True
        else:
            self.debounce_count = 0

        return changed


led = RGBLed()
led.green(0.1)

wlan_init()

button_a = ButtonDebounce(12)
button_b = ButtonDebounce(13)
button_x = ButtonDebounce(14)
button_y = ButtonDebounce(15)

# Clear display
clear()

# On startup set day to today
now = rtc.datetime()
ntp_dow = now[3]

tick = 0
while True:
    # If the day of the week has changed then we need to
    # resync the date and time
    dow = now[3]
    if ntp_dow != dow:
        refreshed_date_time = False
        fed_fish = False
        ntp_dow = dow

    if refreshed_date_time == False:
        refresh_date_time()
        refreshed_date_time = True

    if now[4] >= 8 and not fed_fish:
        feed_fish()

    line3 = ""

    if button_a.debounce() and button_a.state:
        turn_on_display()
        fed_fish = False

    if button_b.debounce() and button_b.state:
        turn_on_display()

    if button_x.debounce() and button_x.state:
        turn_on_display()
        refreshed_date_time = False

    if button_y.debounce() and button_y.state:
        turn_on_display()
        wlan_init()

    if display_on_count > 0:
        display_on_count -= 1

        if display_on_count == 0:
            turn_off_display()

    tick += 1
    if tick > 100:
        tick = 0

        update_display()

        # Get current date time
        now = rtc.datetime()

    time.sleep(0.001)

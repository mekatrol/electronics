import socket
import struct
import select
import gc
from time import gmtime
from config import *
import machine
from http import WebApp, jsonify

from WlanHelper import WlanHelper
from Neopixel import Neopixel
from Neopixel import RED, GREEN, BLUE

sdaPIN = machine.Pin(0)
sclPIN = machine.Pin(1)
i2c = machine.I2C(0, sda=sdaPIN, scl=sclPIN, freq=400000)
led = machine.Pin("LED", machine.Pin.OUT)

try:
    import usocket as socket
except:
    import socket

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

webapp = WebApp()

gc.collect()

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
ntp_host = config["time_server"]

# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
# (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600 if gmtime(0)[0] == 2000 else 2208988800

# Get real time clock
rtc = machine.RTC()

temp_c = -100
date_time = rtc.datetime()

wlan_ssid = config["wlan_ssid"]
wlan_pwd = config["wlan_pwd"]

wlan = WlanHelper()
asyncio.run(wlan.connect(wlan_ssid, wlan_pwd))

is_wlan_connected = wlan.is_connected()


def reg_write(i2c, addr, reg, data):
    """
    Write bytes to the specified register.
    """

    # Construct message
    msg = bytearray()
    msg.append(data)

    # Write out message to register
    i2c.writeto_mem(addr, reg, msg)


def reg_read(i2c, addr, reg, nbytes=1):
    """
    Read byte(s) from specified register. If nbytes > 1, read from consecutive
    registers.
    """

    # Check to make sure caller is asking for 1 or more bytes
    if nbytes < 1:
        return bytearray()

    # Request data from specified register(s) over I2C
    data = i2c.readfrom_mem(addr, reg, nbytes)

    return data


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


def refresh_date_time():
    global is_wlan_connected
    global wlan_ip

    if not is_wlan_connected:
        print(f"Can't refresh date/time without WLAN: {wlan.ip()}")
        return  # Can't refresh date / time if WLAN not connected

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
    print(f"Got date/time from time server: {dt}")

    # rtc.datetime takes tuple (year, month, day, weekday, hours, minutes, seconds, subseconds)
    rtc.datetime((dt[0], dt[1], dt[2], dt[7], dt[3], dt[4], dt[5], dt[6]))


async def update_date_time():
    while True:
        refresh_date_time()
        await asyncio.sleep(10)


async def update_sensors():
    global temp_c
    global date_time
    while True:
        await asyncio.sleep(1)

        # Read data from MCP9808
        data = i2c.readfrom_mem(0x18, 0x05, 2)

        # Convert bytes to word value
        temp_word = ((data[0] & 0x1F) * 256) + data[1]

        # Convert value to +/- values
        if temp_word > 4095:
            temp_word -= 8192

        # Convert to degrees celsius and round to single decimal place
        temp_c = round(temp_word * 0.0625, 1)

        # Print temperature
        print(temp_c)

        date_time = rtc.datetime()
        print(date_time)

        gc.collect()


async def update_neopixels():
    global temp_c
    neopixel = Neopixel(3, 22)
    neopixel.init()

    while True:
        color = GREEN
        if temp_c <= 21:
            color = BLUE
        elif temp_c >= 23:
            color = RED

        neopixel.pixels_fill(color)
        await neopixel.pixels_show()
        await asyncio.sleep(1)


async def check_wlan():
    global wlan

    while True:
        await asyncio.sleep(1)

        is_wlan_connected = wlan.is_connected()

        # If WLAN is not connected then try and reconnect
        if not is_wlan_connected:
            # Initialise WLAN
            print("Initialising LAN...")
            await wlan.connect(wlan_ssid, wlan_pwd)
            gc.collect()


@webapp.route("/", method="GET")
def index(request, response):
    global temp_c
    global date_time
    obj = {}
    obj["temp"] = temp_c
    obj["dateTime"] = date_time
    gc.collect()
    yield from jsonify(response, obj)


# Loop forever
while True:
    loop = asyncio.get_event_loop()
    loop.create_task(update_date_time())
    loop.create_task(update_sensors())
    loop.create_task(check_wlan())
    loop.create_task(update_neopixels())
    loop.create_task(asyncio.start_server(webapp.handle, "0.0.0.0", 80))
    gc.collect()
    loop.run_forever()

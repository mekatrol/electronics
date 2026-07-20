import socket
import struct
import select
import asyncio
import gc
from time import gmtime
from config import *
import machine
from http import WebApp, jsonify
from umqtt.simple import MQTTClient
from mmwave_sensor import MmwaveSensor
from WlanHelper import WlanHelper
from Neopixel import Neopixel
from Neopixel import RED, GREEN, BLUE, BLACK, PURPLE

led = machine.Pin("LED", machine.Pin.OUT)
alarmArmedPin = machine.Pin(21, machine.Pin.IN)
alarmAlarmedPin = machine.Pin(20, machine.Pin.IN)

# Number of LEDs in NeoPixel string
NUM_LEDS = 5

# Panel state values
UNARMED = 'UNARMED'
ARMED = 'ARMED'

# Panel alarm state values
NOT_ALARMED = 'NOTALARMED'
ALARMED = 'ALARMED'

# Default to all OK
alarm_armed_status = UNARMED
alarm_alarmed_status = NOT_ALARMED

# Motion energy levels
motion_energy_value = None

def sync_do_stuff():
    mmwave_sensor = MmwaveSensor()
    neopixel = Neopixel(3, 22)
    neopixel.init()
    
    async def do_stuff():
        while True:
            motion_energy_value = await mmwave_sensor.poll()
            
            neopixel.pixels_fill(BLUE)

            if motion_energy_value is not None:            
                if motion_energy_value < 70:
                    neopixel.pixels_fill(GREEN)
                elif motion_energy_value > 120:
                    neopixel.pixels_fill(RED)
            
            await neopixel.pixels_show()
                        
            await asyncio.sleep(0.001)
        
    asyncio.run(do_stuff())
    
sync_do_stuff()

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

date_time = rtc.datetime()

wlan_ssid = config["wlan_ssid"]
wlan_pwd = config["wlan_pwd"]

wlan = WlanHelper()
asyncio.run(wlan.connect(wlan_ssid, wlan_pwd))

is_wlan_connected = wlan.is_connected()

# Connect MQTT after WLAN as it uses WLAN to communicate
mqtt_host = config["mqtt_host"]
mqtt_clientid = config["mqtt_clientid"]
mqtt_username = config["mqtt_username"]
mqtt_password = config["mqtt_password"]
mqtt_publish_alarm_armed_status_topic = "garage_alarm/armed_status"
mqtt_publish_alarm_alarm_status_topic = "garage_alarm/alarmed_status"

mqtt_client = MQTTClient(
        client_id=mqtt_clientid,
        server=mqtt_host,
        user=mqtt_username,
        password=mqtt_password)

mqtt_client.connect()

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
        await asyncio.sleep(5)


async def update_state():
    global date_time
    global alarm_armed_status
    global alarm_alarmed_status
    while True:
        await asyncio.sleep(1)

        date_time = rtc.datetime()
        
        # Default to unarmed state
        alarm_armed_status = UNARMED
        alarm_alarmed_status = NOT_ALARMED
        
        # Inputs are pulled low to activate state
        if alarmArmedPin.value() == 0:
            alarm_armed_status = ARMED
            
        if alarmAlarmedPin.value() == 0:            
            alarm_alarmed_status = ALARMED

        gc.collect()

async def publish_mqtt():
    global mqtt_client
    
    while True:           
        mqtt_client.publish(mqtt_publish_alarm_armed_status_topic, alarm_armed_status.lower())
        mqtt_client.publish(mqtt_publish_alarm_alarm_status_topic, alarm_alarmed_status.lower())
        
        await asyncio.sleep(5)
        
async def update_mmwave_sensor():
    global motion_energy_value
    
    mmwave_sensor = MmwaveSensor()
    while True:
        motion_energy_value = await mmwave_sensor.poll()
        await asyncio.sleep(0.001)

async def update_neopixels():
    global alarm_alarmed_status
    global motion_energy_value
    
    neopixel = Neopixel(NUM_LEDS, 22)
    neopixel.init()
    toggle_off = False
    rotate = 0
    rotate_direction = 1

    while True:
        energy = 0
        
        if motion_energy_value is not None:
            energy = motion_energy_value
        
        if alarm_alarmed_status == ALARMED or energy > 120:
            color = RED
            toggle_off = not toggle_off
            neopixel.pixels_fill(BLACK)
            if not toggle_off:
                neopixel.pixels_set(1, RED)
                neopixel.pixels_set(3, RED)
            else:
                neopixel.pixels_set(0, RED)
                neopixel.pixels_set(2, RED)
                neopixel.pixels_set(4, RED)

        elif alarm_armed_status == ARMED:
            color = RED
            toggle_off = False
            neopixel.pixels_fill(BLACK)
            neopixel.pixels_set(rotate, RED)
                                                                    
        elif alarm_armed_status == UNARMED:
            color = GREEN
            toggle_off = False
            neopixel.pixels_fill(BLACK)
            neopixel.pixels_set(rotate, GREEN)
                
        else:    
            color = PURPLE
            toggle_off = not toggle_off
            neopixel.pixels_fill(color)

        # Update rotating LED, only active if rotating == True
        rotate = rotate + rotate_direction
        if rotate < 0:
            rotate = 1
            rotate_direction = rotate_direction * -1
        elif rotate >= NUM_LEDS:
            rotate = NUM_LEDS - 2 # Step back to LED before last LED
            rotate_direction = rotate_direction * -1
                
        await neopixel.pixels_show()
        await asyncio.sleep(0.2)


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
    global date_time
    global alarm_armed_status
    global alarm_alarmed_status
    
    obj = {}
    obj["dateTime"] = date_time
    obj["alarmArmedStatus"] = alarm_armed_status.lower()
    obj["alarmAlarmedStatus"] = alarm_alarmed_status.lower()
    gc.collect()
    yield from jsonify(response, obj)


# Loop forever
while True:
    loop = asyncio.get_event_loop()
    loop.create_task(update_date_time())
    loop.create_task(update_state())
    loop.create_task(check_wlan())
    loop.create_task(update_neopixels())
    loop.create_task(publish_mqtt())
    loop.create_task(update_mmwave_sensor())
    loop.create_task(asyncio.start_server(webapp.handle, "0.0.0.0", 80))
    gc.collect()
    loop.run_forever()

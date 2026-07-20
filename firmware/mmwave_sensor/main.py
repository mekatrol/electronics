import machine
import asyncio
from config import *
from mmwave_sensor import MmwaveSensor
from neo_pixel import Neopixel
from neo_pixel import RED, GREEN, BLUE, BLACK, PURPLE

from wlan import WlanHelper
from umqtt.simple import MQTTClient

led = machine.Pin("LED", machine.Pin.OUT)

ip1 = machine.Pin(18, machine.Pin.IN, pull=machine.Pin.PULL_UP)
ip2 = machine.Pin(19, machine.Pin.IN, pull=machine.Pin.PULL_UP)

op1 = machine.Pin(26, machine.Pin.OUT)
op2 = machine.Pin(27, machine.Pin.OUT)

op1.off()
op2.off()

input1 = ip1.value()
input2 = ip2.value()

# Number of LEDs in NeoPixel string
NEO_PIXEL_COUNT = 4

# The GPIO number for LED1 neo pixels
NEO_PIXEL_PIN = 3

# Motion energy levels
motion_energy_value = None

# Start not in alarm and not in warning
in_alarm = False
in_warning = False

# Start not in error
in_error = False

wlan_ssid = config["wlan_ssid"]
wlan_pwd = config["wlan_pwd"]

wlan = WlanHelper()
asyncio.run(wlan.connect(wlan_ssid, wlan_pwd))

is_wlan_connected = wlan.is_connected()

# Set in error if failed to connect to WLAN
if not is_wlan_connected:
    in_error = True

# Connect MQTT after WLAN as it uses WLAN to communicate
mqtt_host = config["mqtt_host"]
mqtt_clientid = config["mqtt_clientid"]
mqtt_username = config["mqtt_username"]
mqtt_password = config["mqtt_password"]
mqtt_motion_energy_topic = config["mqtt_motion_energy_topic"]
mqtt_motion_alarm_topic = config["mqtt_motion_alarm_topic"]
mqtt_input1_topic = config["mqtt_input1_topic"]
mqtt_input2_topic = config["mqtt_input2_topic"]

mqtt_client = MQTTClient(
    client_id=mqtt_clientid,
    server=mqtt_host,
    user=mqtt_username,
    password=mqtt_password)

neopixel = Neopixel(NEO_PIXEL_COUNT, NEO_PIXEL_PIN)

try:
    mqtt_client.connect()
    neopixel.init()
except:
    # In error if cannot initialise devices/connection
    in_error = True



async def io_update():
    global input1
    global input2

    while True:
        input1 = ip1.value()
        input2 = ip2.value()

        await asyncio.sleep(0.25)


async def publish_mqtt():
    global in_error
    global mqtt_client
    global in_alarm
    global motion_energy_value
    global input1
    global input2

    while True:
        try:
            mqtt_client.publish(mqtt_motion_energy_topic, f'{motion_energy_value}')
            mqtt_client.publish(mqtt_motion_alarm_topic, f'{in_alarm}')
            mqtt_client.publish(mqtt_input1_topic, f'{input1}')
            mqtt_client.publish(mqtt_input2_topic, f'{input2}')

            in_error = False
        except:
            in_error = True

        if in_error:
            led.toggle()
        else:
            led.off()

        await asyncio.sleep(1)


async def alarm_output():
    global in_alarm

    current_alarm_output = False

    while True:
        if in_alarm != current_alarm_output and in_alarm == True:
            # Current stat is in alarm
            current_alarm_output = True

            # Turn on alarm output
            op1.on()

            # The alarm output will stay on for at lease 5 seconds
            await asyncio.sleep(5)

        # Current stat is NOT in alarm
        current_alarm_output = False

        # Turn off alarm output
        op1.off()

        # Sleep for a bit
        await asyncio.sleep(0.25)

async def update_neo_pixels():
    global in_alarm
    global in_warning
    global input1
    global input2
    
    pixels = [ GREEN, GREEN, BLUE, RED ]
       
    while True:
        # Give logical names to inputs
        alarm_armed = input1
        alarm_alarmed = input2
        
        if alarm_armed:
            pixels[0] = RED
        else:
            pixels[0] = GREEN

        if alarm_alarmed:
            pixels[1] = RED
        else:
            pixels[1] = GREEN

        if in_alarm:
            pixels[2] = RED
            pixels[3] = RED
        elif in_warning:
            pixels[2] = BLUE
            pixels[3] = BLUE
        else:
            pixels[2] = GREEN
            pixels[3] = GREEN
                
        for i, color in enumerate(pixels):
            neopixel.pixels_set(i, color)
        
        await neopixel.pixels_show()
        await asyncio.sleep(0.1)
            

async def poll_sensor():
    global in_alarm
    global in_warning
    global motion_energy_value

    mmwave_sensor = MmwaveSensor(uart=1, baudrate=115200, tx=8, rx=9)

    # Assume not in alarm, but in warning
    in_alarm = False
    in_warning = True

    interval = 0.001
    tick_threshold = 1 / (interval * 10)

    while True:
        motion_energy_value = mmwave_sensor.poll()

        if motion_energy_value is not None:
            # Less than warning (and error) threshold?
            if motion_energy_value < 70:
                in_alarm = False
                in_warning = False
            # Above error threshold?
            elif motion_energy_value > 120:
                in_alarm = True
                in_warning = False

        await asyncio.sleep(0.001)


# Loop forever
while True:
    loop = asyncio.get_event_loop()
    loop.create_task(io_update())
    loop.create_task(alarm_output())
    loop.create_task(poll_sensor())
    loop.create_task(publish_mqtt())
    loop.create_task(update_neo_pixels())
    loop.run_forever()

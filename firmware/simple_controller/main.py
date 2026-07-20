from machine import Pin
from wlan import Wlan
from config import config
import asyncio

pin = Pin("LED", Pin.OUT)

wlan_ssid = config["wlan_ssid"]
wlan_pwd = config["wlan_pwd"]


async def toggle_led():
    while True:
        pin.toggle()
        await asyncio.sleep(1)


async def wlan_connection():
    wlan = Wlan()

    while True:
        # Check if still connected
        if not wlan.is_connected():
            # If not connected then try connecting
            try:
                print(f"Connecting to WLAN {wlan_ssid}")
                await wlan.connect(wlan_ssid, wlan_pwd)
                print(f"Connected to WLAN {wlan_ssid} with IP {wlan.ip()}")
            except Exception:
                print(f"Failed to connect to WLAN {wlan_ssid}")

        # Sleep for 10 seconds
        await asyncio.sleep(1)


while True:
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(wlan_connection())
        loop.create_task(toggle_led())
        loop.run_forever()
    except KeyboardInterrupt:
        break

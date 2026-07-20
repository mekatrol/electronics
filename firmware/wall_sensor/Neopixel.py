# Example using PIO to drive a set of WS2812 LEDs.

import array
from machine import Pin
import rp2

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)


@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=24,
)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1).side(0)[T3 - 1]
    jmp(not_x, "do_zero").side(1)[T1 - 1]
    jmp("bitloop").side(1)[T2 - 1]
    label("do_zero")
    nop().side(0)[T2 - 1]
    wrap()


class Neopixel:
    def __init__(self, led_count, pin_number, brightness=0.2):
        self._led_count = led_count
        self._pin_number = pin_number
        self._brightness = brightness

    def init(self):
        # Create the state machine for controlling pin
        self._sm = rp2.StateMachine(
            0, ws2812, freq=8_000_000, sideset_base=Pin(self._pin_number)
        )

        # Start the state machine
        self._sm.active(1)

        # Create array to hold each led RGB value
        self._ar = array.array("I", [0 for _ in range(self._led_count)])

    async def pixels_show(self):
        dimmer_ar = array.array("I", [0 for _ in range(self._led_count)])
        for i, c in enumerate(self._ar):
            r = int(((c >> 8) & 0xFF) * self._brightness)
            g = int(((c >> 16) & 0xFF) * self._brightness)
            b = int((c & 0xFF) * self._brightness)
            dimmer_ar[i] = (g << 16) + (r << 8) + b
        self._sm.put(dimmer_ar, 8)
        await asyncio.sleep(0.02)

    def pixels_set(self, i, color):
        self._ar[i] = (color[1] << 16) + (color[0] << 8) + color[2]

    def pixels_fill(self, color):
        for i in range(len(self._ar)):
            self.pixels_set(i, color)

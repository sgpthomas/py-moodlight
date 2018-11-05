#!/usr/bin/env python3

import rpi_ws281x as ws

if  __name__ == "__main__":
    lights = ws.PixelStrip(450, 18, brightness=100)
    lights.begin()
    for i in range(450):
        lights.setPixelColorRGB(i, 0, 0, 0)
    lights.show()

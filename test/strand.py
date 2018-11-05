#!/usr/bin/env python3

import rpi_ws281x as ws
# from rpi_ws281x import Color
from time import sleep
from random import randint
import math
import itertools

import colorsys
from threading import Thread, Lock, Condition

def make_generator(f):
    i = 0
    while True:
        yield f(i)
        i += 1

def cycle_range(lower, upper, step):
    d = step
    i = lower
    while i >= lower:
        yield i
        i += d
        if i >= upper: d *= -1

class Color():
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        self.rgb = True
    
    def bound(i):
        if i < 0: return 0
        if i > 255: return 255
        return i

    def to_hsv(self):
        if self.rgb:
            return tuple(Color.bound(round(i * 255)) for i in colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255))
        else:
            return (self.r, self.g, self.b)

    def to_rgb(self):
        if self.rgb == False:
            return tuple(Color.bound(round(i * 255)) for i in colorsys.hsv_to_rgb(self.r / 255, self.g / 255, self.b / 255))
        else:
            return (self.r, self.g, self.b)
    
    def hsv(h, s, v):
        c = tuple(Color.bound(round(i * 255)) for i in colorsys.hsv_to_rgb(h / 255, s / 255, v / 255))
        c = Color(c[0], c[1], c[2])
        c.rgb = False
        return c

    def rgb(r, g, b):
        return Color(r, g, b)

class LightArray():
    def __init__(self, num, pin, brightness=100):
        self.num = num
        self.pix = ws.PixelStrip(num, pin, brightness=100)
        self.pix.begin()

    def set(self, i, c):
        if i >= 0 and i < self.num:
            self.pix.setPixelColorRGB(i, c.r, c.g, c.b)

    def setRGB(self, i, r, g, b):
        self.set(i, Color(r, g, b))

    def add(self, i, c):
        existing = self.pix.getPixelColorRGB(i)
        self.setRGB(i, (c.r + existing.r) % 255, (c.g + existing.g) % 255, (c.b + existing.b) % 255)

    def sub(self, i, c):
        existing = self.pix.getPixelColorRGB(i)
        self.setRGB(i, (existing.r - c.r) % 255, (existing.g - c.g) % 255, (existing.b - c.b) % 255)

    # def get(self, i, c):
        # return self.pix.getPixelColor()

    # def getRGB(self, i, c):
        # return self.pix.getPixelColorRGB()

    def show(self):
        self.pix.show()

    def clear(self, i):
        if i >= 0 and i < self.num:
            self.setRGB(i, 0, 0, 0)

    def reset(self):
        for i in range(self.num):
            self.clear(i)
        self.show()

    def set_brightness(self, b):
        self.pix.set_brightness()

    def size(self):
        return self.num

def wipe(lights, r, g, b):
    for i in range(lights.size()):
        lights.setRGB(i, r, g, b)
    lights.show()

def chase(lights, packet_size, size, grad_start):
    # c = wheel(grad_start % size)#randint(0, 255))
    grad = 255 / packet_size
    for i in range(size):
        for p in range(packet_size):
            lights.set(i-p, Color.hsv(grad_start, 255-(grad*p), 255-(grad*p)))
        lights.clear(i-packet_size-1)
        lights.show()
        # sleep(0.01)

def wave(lights):
    size = lights.size()
    i = 0
    rate = math.pi * 0.0015
    r = make_generator(lambda x: abs(round(130 * math.sin(0.92 * rate * -x))))
    g = make_generator(lambda x: abs(round(55 * math.sin(4.1 * rate * -x))))
    b = make_generator(lambda x: abs(round(30 * math.sin(1.01 * rate * -x))))
    for c in zip(r, g, b):
        if i > size:
            i = 0 
            lights.show()
            sleep(0.07)
        lights.set(i, Color(c[0], c[1], c[2]))    
        # lights.show()
        i += 1

def pulse(lights, width, psize, hue):
    grad = 255 / psize
    for i in range(width + psize):
        for p in range(psize):
            lights.set(i-p, Color.hsv(hue, 255-(grad*p), 255-(grad*p)))
        sleep(0.015)
        lights.clear(i-psize-1)
        lights.show()

# def comet_pile(lights):
    # size = 450
    # col = randint(0, 255)
    # while size > 0:
        # packet_size = randint(30,100)
        # chase(lights, packet_size, size, col)
        # size -= 10 + 2
        # col += randint(10,40) % 255

def shimmer(lights, dist, bright):
    for i in range(dist):
        lights.set(randint(0, lights.size()), Color.hsv(100, randint(0, bright), 255))

def strange(lights, min_bright, max_bright, step, dist):
    # while True:    # Arjun and Akhil
    for bright in cycle_range(min_bright, max_bright, step):
        for i in range(lights.size()):
            lights.set(i, Color.hsv(40, bright, 255))
            # shimmer(lights, 50, bright)
            for i in range(dist):
                lights.set(randint(0, lights.size()), Color.hsv(100, randint(0, bright), 255))
        lights.show()


def string_lights(lights, min_bright, max_bright):
    for s in range(3):
        for bright in cycle_range(min_bright, max_bright, 1):
            for i in range(s, lights.size(), 3):
                lights.set(i, Color.hsv(23, 169, bright))
            lights.show()
            # print(bright)
            sleep(0.01)
        for i in range(s, lights.size(), 3):
            lights.clear(i)

class Updater(Thread):
    def __init__(self, lights, rate=0.1):
        Thread.__init__(self)
        self.lights = lights
        self.rate = rate

    def run(self):
        while True:
            sleep(self.rate)
            self.lights.show()

class Blub(Thread):
    def __init__(self, lights, const=0.102):
        Thread.__init__(self)
        self.lights = lights
        self.const = const
    
    def run(self):
        while True:
            if randint(0, 4) != 0:
                center = randint(0, self.lights.size())
                radius = randint(1, 100)
                hue = randint(1, 255)
                lights = self.lights
                grad_r = 255 / radius
                const = self.const
                pause = lambda r: sleep((const * ((r / radius)**2)))
                for r in range(radius):
                    c = Color.hsv(hue, 255-(grad_r*r), 255-(grad_r*r))
                    lights.add((center+r)%lights.size(), c)
                    lights.add((center-r)%lights.size(), c)
                    pause(r)
                for r in range(radius, -1, -1):
                    c = Color.hsv(hue, 255-(grad_r*r), 255-(grad_r*r))
                    lights.sub((center+r)%lights.size(), c)
                    lights.sub((center-r)%lights.size(), c)
                    pause(r)
            else:
                sleep(randint(1,5))

def blub(lights, center, radius, hue):
    grad_r = 255 / radius
    const = 0.102
    pause = lambda r: sleep((const * ((r / radius)**2)))
    for r in range(radius):
        lights.set((center+r)%lights.size(), Color.hsv(hue, 255-(grad_r*r), 255-(grad_r*r)))
        lights.set((center-r)%lights.size(), Color.hsv(hue, 255-(grad_r*r), 255-(grad_r*r)))
        # pause(r)
        lights.show()
    for r in range(radius, -1, -1):
        lights.clear((center+r)%lights.size())
        lights.clear((center-r)%lights.size())
        # pause(r)
        lights.show()

def loop(lights):
    # wave(lights)
    # pulse(lights, lights.size(), randint(10, 100), randint(10, 255))
    # string_lights(lights, 50, 110)
    # strange(lights, 0, 200, 2, 50)
    # blub(lights, randint(0, lights.size()), randint(10, 80), randint(0, 255))
    # blub(lights, randint(0,lights.size()), randint(10, 50), randint(0, 255))
    # n = randint(2,8)
    if len(lst) < n:
        b = Blub(lights, barrier)
        b.start()
        lst.append(b)
    # else:
        #lst[randint(0, len(lst)-1)].join()
    # for i in lst:
        # if not i.is_alive(): lst.remove(i)

def main():
    lights = LightArray(450, 18, brightness=100)
    n = 7
    Updater(lights, rate=0.01).start()
    try:
        for i in range(n):
            Blub(lights, const=0.112).start()
        # while True: loop(lights)
    except KeyboardInterrupt:
        #wipe(lights, 0x9F, 0x70, 0x3a)
        # wipe(lights, 0x34, 0x70, 0x44)
        # wipe(lights, 0x98, 0x78, 0x54)
        lights.reset()

if __name__ == "__main__":
    main()

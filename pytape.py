import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from gpiozero import Button
from signal import pause

import subprocess
import requests

class Web:
    def check_uploads():
        r = requests.get('')

        print(r.status_code)
        print(r.json())

class PyTape:
    def __init__(self):
        self.menu_items = ['check for sounds', 'play from start', 'tape control']
        self.menu_index = 0
        self.menu_length = 3
        self.menu_range_start = 0
        self.menu_range_end = 2

        self.b1 = Button('GPIO21')
        self.b2 = Button('GPIO20')
        self.b3 = Button('GPIO16')
        self.b4 = Button('GPIO12')

        self.display = Adafruit_SSD1306.SSD1306_128_32(rst=None)

        self.display.begin()
        self.display.clear()
        self.display.display()

        # Some other nice fonts to try: http://www.dafont.com/bitmap.php
        # font = ImageFont.truetype('Minecraftia.ttf', 8)
        self.font = ImageFont.load_default()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = self.display.width
        self.height = self.display.height
        self.image = Image.new('1', (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, self.height), outline = 0, fill = 0)

        cmd = "iwgetid -r"
        ssid = subprocess.check_output(cmd, shell = True )
        self.draw.text((0, -2), str(ssid), font=self.font, fill=255)

    def menu_up(self):
        if self.menu_index > 0:
            self.menu_index -= 1
            self.draw_menu()

    def menu_down(self):
        if self.menu_index < len(self.menu_items) - 1:
            self.menu_index += 1
            self.draw_menu()

    def menu_in(self):
        obj = self.menu_items[menu_index]

        if callable(obj):
            obj()

    def menu_out(self):
        print('blep')

    def menu(self):
        self.menu_index = 0
        self.b1.when_pressed = self.menu_up
        self.b2.when_pressed = self.menu_down
        self.b3.when_pressed = self.menu_out
        self.b4.when_pressed = self.menu_in
        self.draw_menu()

    def draw_menu(self):
        if self.menu_index < self.menu_range_start:
            self.menu_range_start = self.menu_index
            self.menu_range_end = self.menu_index + 2
        elif self.menu_index > self.menu_range_end:
            self.menu_range_start = self.menu_index - 2
            self.menu_range_end = self.menu_index

        self.draw.rectangle((0, 8, self.width, self.height), outline = 0, fill = 0)

        self.menu_item_y = 6

        for idx in range(self.menu_range_start, self.menu_range_end + 1):
            leader = "-> " if idx == self.menu_index else "   "
            self.draw.text((0, self.menu_item_y), leader + self.menu_items[idx], font=self.font, fill=255)
            self.menu_item_y += 8

        self.display.image(self.image)
        self.display.display()

if __name__ == "__main__":
    pytape = PyTape()
    pytape.menu()
    pause()

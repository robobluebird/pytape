import time
import subprocess

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from gpiozero import Button
from signal import pause

from tapecontrol import TapeControl 
from web import Web

class PyTape:
    def do_nothing(self):
        return

    def __init__(self):
        self.text_items = []

        self.ignore_next = False
        self.lock = False

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

        self.tc = TapeControl()
        self.w = Web()

    def connection_info(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, 8), outline = 0, fill = 0)

        cmd = "iwgetid -r"
        ssid = subprocess.check_output(cmd, shell = True )
        self.draw.text((0, -2), str(ssid), font=self.font, fill=255)

        self.display.image(self.image)
        self.display.display()

    def main_menu(self):
        def w():
            if self.lock:
                return
            
            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                self.web()

            self.lock = False

        def t():
            if self.lock:
                return
            
            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                self.tape()

            self.lock = False

        self.b1.when_released = w
        self.b2.when_released = t
        self.b3.when_released = self.do_nothing
        self.b4.when_released = self.do_nothing

        self.text_items = ["1. Web", "2. Tape", "3. Conn"]

        self.draw_menu()

    def tape(self):
        def p():
            if self.lock:
                return

            self.lock = True

            if self.b2.is_pressed:
                self.ignore_next = True
                self.tc.rec()
            else:
                self.tc.play()

            self.lock = False

        def s():
            if self.lock:
                print "locked!"
                return
            
            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                self.tc.stop()

            self.lock = False

        def ff():
            if self.lock:
                return
            
            self.lock = True

            if self.b2.is_pressed:
                self.ignore_next = True
                self.lock = False
                self.main_menu()
            else:
                self.tc.ff()

            self.lock = False

        def rw():
            if self.lock:
                return

            self.lock = True
            self.tc.rw()
            self.lock = False

        self.b1.when_released = p
        self.b2.when_released = s
        self.b3.when_released = ff
        self.b4.when_released = rw

        self.text_items = [
            "1. Play",
            "2. Stop",
            "3. FF",
            "4. RW",
            "2 + 1. Rec",
            "2 + 3. Back"
        ]

        self.draw_menu()

    def web(self):
        def b():
            if self.lock:
                return

            self.lock = True
            self.w.stop()
            self.main_menu()
            self.lock = False

        self.b1.when_released = b
        self.b2.when_released = self.do_nothing
        self.b3.when_released = self.do_nothing
        self.b4.when_released = self.do_nothing

        self.text_items = ["1. Back"]
        self.draw_menu(y=14)
        self.w.start(self)

    def update(self):
        # update 2nd and 3rd lines of display
        return

    def draw_menu(self, y=-2):
        self.draw.rectangle((0, 8, self.width, self.height), outline = 0, fill = 0)

        for idx, item in enumerate(self.text_items):
            x = 0

            if idx % 2 == 0:
                y += 8
            else:
                x = 64

            self.draw.text((x, y), item, font=self.font, fill=255)

        self.display.image(self.image)
        self.display.display()

if __name__ == "__main__":
    pytape = PyTape()
    pytape.connection_info()
    pytape.main_menu()
    pause()

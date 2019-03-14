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
        self.chars = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789~!@#$%^&*()_+-=[]\\{}E9|;':\",./<>?"
        self.char_index = 0
        self.password = ""
        self.selected_network = ""

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

        self.normal_font = ImageFont.truetype("dos.ttf", 11)
        self.big_font    = ImageFont.truetype("dos.ttf", 20)

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

        ssid = subprocess.check_output("iwgetid -r", shell = True )
        self.draw.text((0, 0), str(ssid), font=self.normal_font, fill=255)

        self.display.image(self.image)
        self.display.display()

    def main_menu(self):
        self.connection_info()

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

        def n():
            if self.lock:
                return

            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                self.choose_network()

            self.lock = False

        self.b1.when_released = w
        self.b2.when_released = t
        self.b3.when_released = n
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
        self.draw_menu(y=16)
        self.w.start(self)

    def choose_network(self):
        cmd = "sudo iw dev wlan0 scan | grep SSID"

        self.networks = subprocess.check_output(cmd, shell = True ).split('\n')
        self.networks = filter(lambda x: len(x) > 0, self.networks)
        self.networks = map(lambda x: x.split(':')[1].strip(), self.networks)

        self.menu_index = 0
        self.menu_start = 0
        self.menu_end = len(self.networks) - 1 if len(self.networks) < 3 else 2

        def adjust_indices():
            if self.menu_index < self.menu_start:
                self.menu_start = self.menu_index
                self.menu_end = self.menu_index + 2
            elif self.menu_index > self.menu_end:
                self.menu_start = self.menu_index - 2
                self.menu_end = self.menu_index

        def u():
            if self.menu_index > 0:
                self.menu_index -= 1
                adjust_indices()
                self.draw_networks()

        def d():
            if self.menu_index < len(self.networks) - 1:
                self.menu_index += 1
                adjust_indices()
                self.draw_networks()

        def c():
            self.selected_network = self.networks[self.menu_index]
            self.enter_password()

        def b():
            self.selected_network = ""
            self.main_menu()

        self.b1.when_released = u
        self.b2.when_released = d
        self.b3.when_released = c
        self.b4.when_released = b

        self.draw_networks()

    def draw_networks(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline = 0, fill = 0)
        self.draw.text((0, 0), "3. Go 4. Back 4 + 3. Rescan", font=self.normal_font, fill=255)
        y = 8

        for idx in range(self.menu_start, self.menu_end + 1):
            leader = "-> " if idx == self.menu_index else "   "
            self.draw.text((0, y), leader + self.networks[idx], font=self.normal_font, fill=255)
            y += 8

        self.display.image(self.image)
        self.display.display()

    def enter_password(self):
        self.password = ""

        def l():
            if self.char_index > 0:
                self.char_index -= 1
                self.draw_password()

        def r():
            if self.char_index < len(self.chars):
                self.char_index += 1
                self.draw_password()

        def a():
            if self.ignore_next:
                self.ignore_next = False
                return
            else:
                self.password += self.chars[self.char_index]
                self.draw_password()

        def b():
            if self.b3.is_pressed:
                self.ignore_next = True
                self.connect()
            else:
                if len(self.password) > 0:
                    self.password = self.password[:-1]
                    self.draw_password()

        self.b1.when_released = l
        self.b2.when_released = r
        self.b3.when_released = a
        self.b4.when_released = b

        self.draw_password()

    def connect(self):
        [self.selected_network, self.password]

        lines = [
                    "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev",
                    "update_config=1",
                    "",
                    "network={",
                    '\tssid="%s"' % self.selected_network,
                    '\tpsk="%s"' % self.password,
                    "}"
                ]

        conf = open("/etc/wpa_supplicant/wpa_supplicant.conf", 'w')
        conf.writelines(lines)
        conf.close()

        subprocess.check_output("sudo ip link set wlan0 down", shell = True )

        subprocess.check_output("sudo ip link set wlan0 up", shell = True )

        result = subprocess.check_output("iw wlan0 link", shell=True)

        while ("SSID: %s" % self.selected_network) not in result:
            result = subprocess.check_output("iw wlan0 link", shell=True)
            print "waiting..."
            time.sleep(1)

        print "done! waiting again..."

        time.sleep(5)

        print "go!"

        self.main_menu()
        # figure out why fetching of ssid in main menu doesn't work after this...

    def draw_password(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline = 0, fill = 0)

        self.draw.text((0, 0), self.selected_network, font=self.normal_font, fill=255)
        self.draw.text((0, 8), self.password, font=self.normal_font, fill=255)

        i = 1
        prefix = ""
        postfix = ""

        while i < 8 and self.char_index - i >= 0:
            prefix = self.chars[self.char_index - i] + prefix
            i += 1

        px = 49 - (5 * i)

        i = 1
        
        while i < 8 and self.char_index + i < len(self.chars):
            postfix += self.chars[self.char_index + i]
            i += 1

        self.draw.text((px, 24), prefix, font=self.normal_font, fill=255)
        self.draw.text((54, 16), self.chars[self.char_index], font=self.big_font, fill=255)
        self.draw.text((69, 24), postfix, font=self.normal_font, fill=255)

        self.display.image(self.image)
        self.display.display()

    def update(self, message):
        lines = ([], [])
        i = 0
        j = 0
        parts = message.split()
        parts.reverse()

        lines[0].append(parts.pop())

        while len(parts) > 0:
            part = parts.pop()

            new_len = len(part) + len(" ".join(lines[j])) + 1

            if new_len <= 20 or j == 1:
                lines[j].append(part)
            else:
                j += 1

        self.draw.rectangle((0, 8, self.width, 16), outline = 0, fill = 0)
        self.draw.text((0, 8), " ".join(lines[0]), font=self.normal_font, fill=255)
        self.draw.text((0, 16), " ".join(lines[1]), font=self.normal_font, fill=255)
        self.display.image(self.image)
        self.display.display()

    def draw_menu(self, y=0):
        self.draw.rectangle((0, 8, self.width, self.height), outline = 0, fill = 0)

        for idx, item in enumerate(self.text_items):
            x = 0

            if idx % 2 == 0:
                y += 8
            else:
                x = 64

            self.draw.text((x, y), item, font=self.normal_font, fill=255)

        self.display.image(self.image)
        self.display.display()

if __name__ == "__main__":
    pytape = PyTape()
    pytape.connection_info()
    pytape.main_menu()
    pause()

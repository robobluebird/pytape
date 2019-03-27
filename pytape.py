import time
import subprocess

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from gpiozero import Button, DigitalInputDevice
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
        self.text_entry = ""
        self.selected_network = ""
        self.name = ""
        self.ticks = 0
        self.reason_for_waiting = None

        self.ignore_next = False
        self.lock = False

        self.b1 = Button('GPIO21')
        self.b2 = Button('GPIO20')
        self.b3 = Button('GPIO16')
        self.b4 = Button('GPIO12')

        self.io1 = DigitalInputDevice('GPIO17')
        self.io1.when_activated = self.message_available

        self.io2 = DigitalInputDevice('GPIO27')
        self.io2.when_activated = self.end_of_tape

        self.display = Adafruit_SSD1306.SSD1306_128_32(rst=None)
        self.display.begin()
        self.display.clear()
        self.display.display()

        f = "/home/pi/Code/python/pytape/dos.ttf"
        self.normal_font = ImageFont.truetype(f, 10)
        self.big_font    = ImageFont.truetype(f, 16)

        # Create blank image for drawin
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = self.display.width
        self.height = self.display.height
        self.image = Image.new('1', (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, self.height), outline = 0, fill = 0)

        self.tc = TapeControl()
        self.w = Web(owner=self)

    def message_available(self):
        result = self.tc.get_message()

        if ":" in result:
            key, value = result.split(':')

            if key == "ticks":
                if self.reason_for_waiting == 'analysis':
                    self.ticks = int(value)
                    self.enter_text('name ur tape', self.new_tape)
        else:
            self.update(result, True)
            time.sleep(3)
            self.main_menu()

    def new_tape(self):
        print "!!!"
        print self.text_entry
        print self.ticks
        print "!!!"
        self.update('working on it...', True, True)
        self.w.create(self.text_entry, self.ticks)
        self.name = self.text_entry
        self.text_entry = ""
        self.tape_screen()

    def tape_screen(self):
        # what do we want to show when you've "loaded" a tape?

    def start_of_tape(self):
        self.update('At the start!', True)
        time.sleep(3)
        self.main_menu()

    def end_of_tape(self):
        self.update('At the end!', True)
        time.sleep(3)
        self.main_menu()

    def connection_info(self):
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
            elif self.b1.is_pressed:
                self.ignore_next = True
                self.lock = True
                self.update('Analyzing tape...', True)
                self.reason_for_waiting = 'analysis'
                self.tc.new_tape()
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

        def e():
            if self.lock:
                return

            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                self.tc.start_of_tape()

            self.lock = False

        self.b1.when_released = w
        self.b2.when_released = t
        self.b3.when_released = n
        self.b4.when_released = e

        self.text_items = [
            "1. Web",
            "2. Deck",
            "3. Wifi",
            "4. Rewind",
            "1+2. New",
            "1+3. Load"
        ]

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
            "2+1. Rec",
            "2+3. Back"
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
        self.w.start()

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
            self.enter_text('enter password', self.connect)

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
        y = 9

        for idx in range(self.menu_start, self.menu_end + 1):
            leader = "-> " if idx == self.menu_index else "   "
            self.draw.text((0, y), leader + self.networks[idx], font=self.normal_font, fill=255)
            y += 8

        self.display.image(self.image)
        self.display.display()

    def enter_text(self, title, callback, args={}):
        self.text_entry = ""

        def l():
            if self.char_index > 0:
                self.char_index -= 1
                self.draw_text_entry(title)

        def r():
            if self.char_index < len(self.chars):
                self.char_index += 1
                self.draw_text_entry(title)

        def a():
            if self.ignore_next:
                self.ignore_next = False
                return
            else:
                self.text_entry += self.chars[self.char_index]
                self.draw_text_entry(title)

        def b():
            if self.b3.is_pressed:
                self.ignore_next = True
                callback()
            else:
                if len(self.text_entry) > 0:
                    self.text_entry = self.text_entry[:-1]
                    self.draw_text_entry(title)

        self.b1.when_released = l
        self.b2.when_released = r
        self.b3.when_released = a
        self.b4.when_released = b

        self.draw_text_entry(title)

    def draw_text_entry(self, title):
        self.draw.rectangle((0, 0, self.width, self.height), outline = 0, fill = 0)

        self.draw.text((0, 0), title, font=self.normal_font, fill=255)
        self.draw.text((0, 9), self.text_entry, font=self.normal_font, fill=255)

        i = 1
        prefix = ""
        postfix = ""

        while i < 12 and self.char_index - i >= 0:
            prefix = self.chars[self.char_index - i] + prefix
            i += 1

        px = 60 - (5 * i)

        i = 1
        
        while i < 12 and self.char_index + i < len(self.chars):
            postfix += self.chars[self.char_index + i]
            i += 1

        self.draw.text((px, 24), prefix, font=self.normal_font, fill=255)
        self.draw.text((60, 16), self.chars[self.char_index], font=self.big_font, fill=255)
        self.draw.text((70, 24), postfix, font=self.normal_font, fill=255)

        self.display.image(self.image)
        self.display.display()

    def connect(self):
        lines = [
            "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n",
            "update_config=1\n",
            "\n",
            "network={\n",
            '\tssid="%s"\n' % self.selected_network,
            '\tpsk="%s"\n' % self.text_entry,
            "}\n"
        ]

        conf = open("/etc/wpa_supplicant/wpa_supplicant.conf", 'w')
        conf.writelines(lines)
        conf.close()

        msg = "connecting..."

        self.update(message=msg, full=True)

        subprocess.check_output("sudo ip link set wlan0 down", shell = True )

        subprocess.check_output("sudo ip link set wlan0 up", shell = True )

        result = subprocess.check_output("iw wlan0 link", shell=True)

        while ("SSID: %s" % self.selected_network) not in result:
            result = subprocess.check_output("iw wlan0 link", shell=True)
            time.sleep(1)
            msg += "."
            self.update(message=msg, full=True)

        msg = "done! waiting for connectivity..."

        for i in range(1, 6):
            self.update(message=msg, full=True)
            time.sleep(1)
            msg += "."

        self.main_menu()

    def update(self, message, full=False, top_line=False):
        lines = ([], [])
        max_lines = 2
        i = 0
        j = 0

        parts = message.split()
        parts.reverse()

        lines[0].append(parts.pop())

        while len(parts) > 0:
            lines[j].append(parts.pop())

            if len(" ".join(lines[j])) > 26 and j < max_lines - 1:
                parts.append(lines[j].pop())
                j += 1

        h = 32 if full else 24

        t = 0 if top_line else 9

        self.draw.rectangle((0, t, self.width, h), outline = 0, fill = 0)

        self.draw.text((0, t), " ".join(lines[0]), font=self.normal_font, fill=255)
        self.draw.text((0, t + 8), " ".join(lines[1]), font=self.normal_font, fill=255)
        self.display.image(self.image)
        self.display.display()

    def draw_menu(self, y=0):
        self.draw.rectangle((0, 9, self.width, self.height), outline = 0, fill = 0)

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

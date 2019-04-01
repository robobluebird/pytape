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
        self.name = ""
        self.current_tick = 0
        self.ticks = 0
        self.reason_for_waiting = None
        self.tape = None

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
        self.normal_font = ImageFont.truetype(f, 8)
        self.big_font    = ImageFont.truetype(f, 16)

        self.width = self.display.width
        self.height = self.display.height
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        self.tc = TapeControl()
        self.w = Web(owner=self)

    def message_available(self):
        result = self.tc.get_message()

        if ":" in result:
            key, value = result.split(':')

            if key == "ticks":
                if self.reason_for_waiting == 'analysis':
                    self.ticks = int(value)
                    self.create_tape()
        else:
            self.update(result, True)
            time.sleep(3)
            self.main_menu()

    def new_tape(self):
        self.enter_text('name ur tape', self.check_tape_name)

    def check_tape_name(self):
        if self.w.check_tape_name(self.text_entry):
            self.update('analyzing tape...', True, True)
            self.reason_for_waiting = 'analysis'
            self.tc.new_tape()
        else:
            self.update('tape name taken, try another...', True, True)
            time.sleep(3)
            self.new_tape()

    def create_tape(self):
        self.update('creating tape...', True, True)

        if self.w.create(self.text_entry, self.ticks):
            self.choice = self.text_entry
            self.load_tape()
            self.text_entry = ""
            self.choice = ""
        else:
            self.main_menu()

    def choose_tape(self):
        self.choices = self.w.tapes()
        self.choose_something(self.load_tape, "tapes...")

    def load_tape(self):
        self.display.clear()

        self.tape = self.w.tape(self.choice)
        self.tape['ticks'] = int(self.tape['ticks'])

        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        draw.rectangle([(0, 0), (self.width, self.height)], outline = 0, fill = 0)

        draw.text((0, 0), self.tape['name'], font = self.normal_font, fill = 255)

        msg = ""
        cmd1 = "1. OK"
        cmd2 = "2. Never mind"

        def ok():
            self.tape_screen()

        def back():
            self.tape = None
            self.main_menu()

        if self.tape['side_a']['complete'] == 'false':
            msg = "Insert tape on side A"
        elif self.tape['side_b']['complete'] == 'false':
            msg = "Insert tape on side B"
        else:
            msg = "Tape full!"
            cmd1 = "1. Start over on side A"

            def ok():
                self.w.restart(self.tape['name'], 'a')
                self.tape_screen()

        self.b1.when_released = ok
        self.b2.when_released = back
        self.b3.when_released = self.do_nothing
        self.b4.when_released = self.do_nothing

        draw.text((0, 8), msg, font=self.normal_font, fill=255)
        draw.text((0, 16), cmd1, font=self.normal_font, fill=255)
        draw.text((0, 24), cmd2, font=self.normal_font, fill=255)

        self.display.image(image)
        self.display.display()

    def tape_screen(self):
        self.display.clear()

        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        draw.rectangle([(0, 0), (self.width, 32)], outline = 0, fill = 0)
        draw.text((0, 0), self.tape['name'], font=self.normal_font, fill=255)
        draw.text((0, 8), "--", font=self.normal_font, fill=255)
        draw.text((0, 24), "blep", font=self.normal_font, fill=255)

        # draw_current_track()
        half_of_all_ticks = self.tape['ticks'] / 2
        percentage = self.ticks / half_of_all_ticks
        width = 10 # percentage * self.width

        draw.rectangle([(-1, 15), (self.width, 24)], outline = 0, fill = 1)
        draw.rectangle([(1, 17), (self.width - 2, 22)], outline = 0, fill = 0)
        draw.rectangle([(1, 17), (1 + width, 22)], outline = 0, fill = 1)

        self.display.image(image)
        self.display.display()

    def draw_current_track(self):
        do_something = "no"

    def start_of_tape(self):
        self.update('At the start!', True)
        time.sleep(3)
        self.main_menu()

    def end_of_tape(self):
        self.update('At the end!', True)
        time.sleep(3)
        self.main_menu()

    def connection_info(self):
        self.draw.rectangle([(0, 7), (self.width, self.height)], outline = 0, fill = 0)

        ssid = subprocess.check_output("iwgetid -r", shell = True )
        self.draw.text((0, 0), str(ssid), font=self.normal_font, fill=255)
        # self.draw.text((0, 8), str(ssid), font=self.normal_font, fill=255)
        # self.draw.text((0, 16), str(ssid), font=self.normal_font, fill=255)
        # self.draw.text((0, 24), str(ssid), font=self.normal_font, fill=255)

        # self.draw.rectangle([(-1, -1), (self.width - 1, 1)], outline = 0, fill = 1)
        # self.draw.rectangle([(-1, 7), (self.width, 9)], outline = 0, fill = 1)
        # self.draw.rectangle([(-1, 15), (self.width, 17)], outline = 0, fill = 1)
        # self.draw.rectangle([(-1, 23), (self.width, 32)], outline = 0, fill = 1)

        self.display.image(self.image)
        self.display.display()

    def main_menu(self):
        self.display.clear()

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
                self.new_tape()
            else:
                self.deck()

            self.lock = False

        def n():
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
                self.update('Loading tapes...', True, True)
                time.sleep(2)
                self.choose_tape()
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

    def deck(self):
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

    def choose_something(self, callback, title=None):
        self.menu_index = 0
        self.menu_start = 0
        self.menu_end = len(self.choices) - 1 if len(self.choices) < 3 else 2

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
                self.draw_choices(title)

        def d():
            if self.menu_index < len(self.choices) - 1:
                self.menu_index += 1
                adjust_indices()
                self.draw_choices(title)

        def c():
            self.choice = self.choices[self.menu_index]
            callback()

        def b():
            self.choice = ""
            self.main_menu()

        self.b1.when_released = u
        self.b2.when_released = d
        self.b3.when_released = c
        self.b4.when_released = b

        self.draw_choices(title)

    def draw_choices(self, title="3. Go 4. Back"):
        self.draw.rectangle((0, 0, self.width, self.height), outline = 0, fill = 0)
        self.draw.text((0, 0), title, font=self.normal_font, fill=255)
        y = 8

        for idx in range(self.menu_start, self.menu_end + 1):
            leader = "-> " if idx == self.menu_index else "   "
            self.draw.text((0, y), leader + self.choices[idx], font=self.normal_font, fill=255)
            y += 8

        self.display.image(self.image)
        self.display.display()

    def choose_network(self):
        cmd = "sudo iw dev wlan0 scan | grep SSID"

        self.choices = subprocess.check_output(cmd, shell = True ).split('\n')
        self.choices = filter(lambda x: len(x) > 0, self.choices)
        self.choices = map(lambda x: x.split(':')[1].strip(), self.choices)

        self.choose_something(self.network_chosen)

    def network_chosen(self):
        self.enter_text('enter password....', self.connect)

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
        print self.choice
        print self.text_entry

        return

        lines = [
            "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n",
            "update_config=1\n",
            "\n",
            "network={\n",
            '\tssid="%s"\n' % self.choice,
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

        while ("SSID: %s" % self.choice) not in result:
            result = subprocess.check_output("iw wlan0 link", shell=True)
            time.sleep(1)
            msg += "."
            self.update(message=msg, full=True)

        msg = "done! waiting for connectivity..."

        for i in range(1, 6):
            self.update(msg, full=True)
            time.sleep(1)
            msg += "."

        self.choices = []
        self.choice = ""
        self.text_entry = ""
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

        t = 0 if top_line else 8

        self.draw.rectangle((0, t, self.width, h), outline = 0, fill = 0)

        self.draw.text((0, t), " ".join(lines[0]), font=self.normal_font, fill=255)
        self.draw.text((0, t + 8), " ".join(lines[1]), font=self.normal_font, fill=255)
        self.display.image(self.image)
        self.display.display()

    def draw_menu(self, y=0):
        self.draw.rectangle((0, 8, self.width, 31), outline = 0, fill = 0)

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
    pytape.main_menu()
    pause()

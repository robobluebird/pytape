import time
import subprocess

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from gpiozero import Button, DigitalInputDevice
from signal import pause
from threading import Thread
import os

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
        self.side = None
        self.do_monitoring = False
        self.thread = None
        self.process = None
        self.mid_line = ""
        self.bottom_line = ""
        self.show_track_listing = False
        self.filepath = None
        self.name = None
        self.recording = False

        self.ignore_next = False
        self.lock = False

        self.b1 = Button('GPIO21')
        self.b2 = Button('GPIO20')
        self.b3 = Button('GPIO16')
        self.b4 = Button('GPIO12')

        self.io1 = DigitalInputDevice('GPIO17')
        self.io1.when_activated = self.message_available

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
                ticks = int(value)

                if self.reason_for_waiting == 'analysis':
                    self.ticks = ticks
                    self.reason_for_waiting = None
                    self.create_tape()
                elif self.reason_for_waiting == 'advance':
                    self.ticks = ticks
                    self.reason_for_waiting = None
                    self.tape_screen(message = "", track_line = self.tick_status())
                elif self.tape != None:
                    self.tape_screen(extra_ticks = ticks)
        elif result == "end":
            if self.process != None:
                self.process.kill()
                self.process = None

            result = self.tc.get_ticks()

            if self.side == 'a':
                vals = result.split(':')

                while len(vals) != 2:
                    result = self.tc.get_ticks()
                    vals = result.split(':')

                ticks = int(vals[1])
                probable_time_skip = 3 * ticks # ~3 ticks per second
                self.record(message = "continuing...", offset = probable_time_skip)
            else:
                self.w.update(self.tape['name'], self.side, complete = True)
                self.choice = self.tape['name']
                self.load_tape()
        elif result == "start":
            if self.reason_for_waiting == 'start':
                self.reason_for_waiting = None
                self.ticks = 0
                self.tape_screen(message = "", track_line = self.tick_status())

    def record(self, message = "recording...", offset = 0):
        self.tape_screen(message = message, track_line = self.name)

        self.tc.start_recording()

        self.process = subprocess.Popen(['play', self.filepath])

        while self.process.poll() == None:
            pass

        self.process = None

        self.tc.stop_recording()

        self.w.mark(self.tape['name'], self.name)

        os.remove(self.filepath)

        self.filepath = None

        result = self.tc.get_ticks()

        vals = result.split(':')

        while len(vals) != 2:
            result = self.tc.get_ticks()
            vals = result.split(':')

        ticks = int(vals[1])

        self.ticks += ticks

        tape = self.w.update(self.tape['name'], self.side, filename = self.name, ticks = ticks)

        self.name = None

        if tape:
            self.tape = tape

        self.tape_screen(message = "", track_line = self.tick_status())

    def tick_status(self):
        return "(%d/%s)" % (self.ticks, self.tape['ticks'])

    def advance_to_current_progress(self):
        side = "side_%s" % self.side
        progress = reduce(lambda x, y: x + y, map(lambda x: int(x['ticks']), self.tape[side]['tracks']), 0)
        self.reason_for_waiting = 'advance'
        self.tc.advance(progress)

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
            self.update("getting ready...", top_line = True, full = True)
            self.advance_to_current_progress()

        def back():
            self.tape = None
            self.main_menu()

        if not self.tape['side_a']['complete']:
            msg = "Insert tape on side A"
            self.side = 'a'
        elif not self.tape['side_b']['complete']:
            msg = "Insert tape on side B"
            self.side = 'b'
        else:
            msg = "Tape full!"
            cmd1 = "1. Never mind"
            self.side = None

            def ok():
                self.tape = None
                self.main_menu()

        self.b1.when_released = ok
        self.b2.when_released = back
        self.b3.when_released = self.do_nothing
        self.b4.when_released = self.do_nothing

        draw.text((0, 8), msg, font = self.normal_font, fill = 255)
        draw.text((0, 16), msg, font = self.normal_font, fill = 255)
        draw.text((0, 24), msg, font = self.normal_font, fill = 255)

        self.display.image(image)
        self.display.display()

    def tape_screen(self, message = None, track_line = None, extra_ticks = 0, discern_track = False):
        self.display.clear()

        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        draw.rectangle([(0, 0), (self.width, 32)], outline = 0, fill = 0)

        tape_name = self.tape['name'] + (" (side %s)" % self.side)
        draw.text((0, 0), tape_name, font = self.normal_font, fill = 255)

        if track_line != None:
            self.mid_line = track_line
        else:
            if self.show_track_listing:
                t = 0
                tracks = self.tape["side_%s" % self.side]['tracks']
                track_times = []

                for track in tracks:
                    track_times.append([track['name'], t, t + track['ticks']])
                    t += track['ticks']

                self.mid_line = next((x[0] for x in track_times if self.ticks >= x[1] and self.ticks <= x[2]), 'no track')

        draw.text((0, 8), self.mid_line, font = self.normal_font, fill = 255)

        percentage = float(self.ticks + extra_ticks) / int(self.tape['ticks'])
        right_bound = percentage * (self.width - 2)

        print percentage
        print self.width - 2
        print right_bound

        if right_bound < 1:
            right_bound = 1

        draw.rectangle([(-1, 15), (self.width, 24)], outline = 0, fill = 1)
        draw.rectangle([(1, 17), (self.width - 2, 22)], outline = 0, fill = 0)
        draw.rectangle([(1, 17), (right_bound, 22)], outline = 0, fill = 1)

        if message != None:
            self.bottom_line = message
        
        draw.text((0, 24), self.bottom_line, font = self.normal_font, fill = 255)

        self.display.image(image)
        self.display.display()

        self.b1.when_released = self.start_monitoring
        self.b2.when_released = self.stop_monitoring
        self.b3.when_released = self.do_nothing
        self.b4.when_released = self.home

    def start_monitoring(self):
        self.thread = Thread(target = self.monitor)
        self.thread.start()

    def stop_monitoring(self):
        self.tape_screen(message = "stopping...")
        self.do_monitoring = False
        self.thread.join()
        self.tape_screen(track_line = self.tick_status(), message = "")

    def home(self):
        if self.do_monitoring:
            self.stop_monitoring()
        self.tape = None
        self.main_menu()

    def monitor(self):
        if self.tape == None:
            self.tape_screen(message = "nothing to monitor...")
            return

        self.do_monitoring = True

        while self.do_monitoring:
            self.tape_screen(message = "checking the web...")

            uploads = self.w.uploads(self.tape['name'])

            if len(uploads) > 0:
                self.name = uploads[0]

                self.filepath = "/home/pi/%s" % self.name

                self.tape_screen(message = "downloading...", track_line = self.name)

                self.w.download(self.tape['name'], self.name, self.filepath)

                self.record()
            else:
                self.tape_screen("nothing to do!")

            time.sleep(10)

    def connection_info(self):
        self.draw.rectangle([(0, 0), (self.width, self.height)], outline = 0, fill = 0)

        try:
            ssid = subprocess.check_output("iwgetid -r", shell = True )
        except subprocess.CalledProcessError:
            ssid = "not connected!"

        self.draw.text((0, 0), str(ssid), font=self.normal_font, fill=255)

        self.display.image(self.image)
        self.display.display()

    def main_menu(self):
        self.display.clear()

        self.connection_info()

        def nt():
            if self.lock:
                return
            
            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                self.new_tape()

            self.lock = False

        def lt():
            if self.lock:
                return
            
            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                self.update("loading tapes...", top_line = True, full = True)
                self.choose_tape()

            self.lock = False

        def wifi():
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

        def rec():
            if self.lock:
                return
            
            self.lock = True

            if self.ignore_next:
                self.ignore_next = False
                self.lock = False
                return
            else:
                if self.recording:
                    self.recording = False
                    self.tc.stop_recording()
                else:
                    self.recording = True
                    self.tc.start_recording()

            self.lock = False


        self.b1.when_released = nt
        self.b2.when_released = lt
        self.b3.when_released = wifi
        self.b4.when_released = rec

        self.text_items = ["1. New Tape", "2. Load Tape", "3. Wifi", "4. Deck"]
        self.draw_menu()
            
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

        self.choose_something(self.network_chosen, "select network...")

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

        self.update("config saved!", top_line = True)
        self.update("rebooting for it to take effect. sorry for the wait...", full = True)

        subprocess.check_output("sudo reboot now", shell = True)

    def update(self, message, full=False, top_line=False, bottom_line=False, big=False):
        if bottom_line:
            self.draw.rectangle([(0, 24), (0, 32)], outline = 0, fill = 0)

            font = self.normal_font

            if big:
                font = self.bit_font

            self.draw.text((0, 24), message, font=font, fill=255)
            self.display.image(self.image)
            self.display.display()
            return

        lines = ([], [], [])
        max_lines = 3
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
        self.draw.text((0, t + 16), " ".join(lines[2]), font=self.normal_font, fill=255)

        self.display.image(self.image)
        self.display.display()

    def draw_menu(self, y=0):
        self.draw.rectangle([(0, 8), (self.width, 31)], outline = 0, fill = 0)

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

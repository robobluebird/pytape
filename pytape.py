import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from gpiozero import Button
from signal import pause

import subprocess

b1 = Button('GPIO21')
b2 = Button('GPIO20')
b3 = Button('GPIO16')
b4 = Button('GPIO12')

menu_index = 0
menu_length = 3
menu_items = ["first", "second", "third", "fourth"]
menu_range_start = 0
menu_range_end = 2

def menu_up():
    global menu_index

    if menu_index > 0:
        menu_index -= 1
        draw_menu()

def menu_down():
    global menu_index

    if menu_index < len(menu_items) - 1:
        menu_index += 1
        draw_menu()

def menu_in():
    obj = globals(menu_items[menu_index])

    if callable(obj):
        obj()

def menu_out():
    print('blep')

def menu():
    menu_index = 0
    b1.when_pressed = menu_up
    b2.when_pressed = menu_down
    b3.when_pressed = menu_out
    b4.when_pressed = menu_in
    draw_menu()

def draw_menu():
    global menu_range_start
    global menu_range_end

    if menu_index < menu_range_start:
        menu_range_start = menu_index
        menu_range_end = menu_index + 2
    elif menu_index > menu_range_end:
        menu_range_start = menu_index - 2
        menu_range_end = menu_index

    draw.rectangle((0, 8, width, height), outline = 0, fill = 0)

    menu_item_y = 6

    for idx in range(menu_range_start, menu_range_end + 1):
        leader = "-> " if idx == menu_index else "   "
        draw.text((0, menu_item_y), leader + menu_items[idx], font=font, fill=255)
        menu_item_y += 8

    display.image(image)
    display.display()

display = Adafruit_SSD1306.SSD1306_128_32(rst=None)

display.begin()
display.clear()
display.display()

# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)
font = ImageFont.load_default()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = display.width
height = display.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline = 0, fill = 0)

cmd = "iwgetid -r"
ssid = subprocess.check_output(cmd, shell = True )
draw.text((0, -2), str(ssid), font=font, fill=255)

menu()

display.image(image)
display.display()

pause()

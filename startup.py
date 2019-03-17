import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import sys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

display = Adafruit_SSD1306.SSD1306_128_32(rst=None)

display.begin()
display.clear()
display.display()

width = display.width
height = display.height
image = Image.new('1', (width, height))
font = ImageFont.truetype('/home/pi/Code/python/pytape/dos.ttf', 8)
draw = ImageDraw.Draw(image)

draw.rectangle((0, 0, width, height), outline = 0, fill = 0)

draw.text((0, 0), "Starting up...", font=font, fill=255)

display.image(image)
display.display()

sys.exit()

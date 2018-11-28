# NextBus scrolling marquee display for Adafruit RGB LED matrix (64x32).
# Requires rgbmatrix.so library: github.com/adafruit/rpi-rgb-led-matrix

import atexit
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import math
import os
import time
#from predict import predict
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Configurable stuff ---------------------------------------------------------

width		  = 128  # Matrix size (pixels) -- change for different matrix
height		 = 32  # types (incl. tiling).  Other code may need tweaks.
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'
options.gpio_slowdown = 2

matrix = RGBMatrix(options = options)
offscreen_canvas = matrix.CreateFrameCanvas()
fps			= 20  # Scrolling speed (ish)

routeColor	 = (255, 255, 255) # Color for route labels (usu. numbers)
descColor	  = (110, 110, 110) # " for route direction/description
longTimeColor  = (  0, 255,   0) # Ample arrival time = green
midTimeColor   = (255, 255,   0) # Medium arrival time = yellow
shortTimeColor = (255,   0,   0) # Short arrival time = red
minsColor	  = (110, 110, 110) # Commans and 'minutes' labels
noTimesColor   = (  0,   0, 255) # No predictions = blue

# TrueType fonts are a bit too much for the Pi to handle -- slow updates and
# it's hard to get them looking good at small sizes.  A small bitmap version
# of Helvetica Regular taken from X11R6 standard distribution works well:
#font		   = ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + '/helvR08.pil')
font		   = ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + '/fonts/12x24.pil')
fontYoffset	= -2  # Scoot up a couple lines so descenders aren't cropped


# Main application -----------------------------------------------------------

# Drawing takes place in offscreen buffer to prevent flicker
image	   = Image.new('RGB', (width, height))
draw		= ImageDraw.Draw(image)
currentTime = 0.0
prevTime	= 0.0

# Clear matrix on exit.  Otherwise it's annoying if you need to break and
# fiddle with some code while LEDs are blinding you.
def clearOnExit():
	matrix.Clear()

atexit.register(clearOnExit)

# Initialization done; loop forever ------------------------------------------

#fdir = '/usr/share/fonts/truetype/freefont/'
fdir = 'fonts/'
dirs = os.listdir(fdir)
for file in dirs:
    if file.endswith(".ttf"):
        font		   = ImageFont.truetype(fdir+file, 13) 
    elif file.endswith(".pil"):
        font		   = ImageFont.load(fdir+file) 
    else:
        continue;
    # Clear background
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

    print(file)
    draw.text((0,2), "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", font=font, fill=minsColor)
    # Try to keep timing uniform-ish; rather than sleeping a fixed time,
    # interval since last frame is calculated, the gap time between this
    # and desired frames/sec determines sleep time...occasionally if busy
    # (e.g. polling server) there'll be no sleep at all.
    currentTime = time.time()
    timeDelta   = (1.0 / fps) - (currentTime - prevTime)
    if(timeDelta > 0.0):
        time.sleep(timeDelta)
    prevTime = currentTime

    # Offscreen buffer is copied to screen
    #matrix.SetImage(image.im.id, 0, 0)
    offscreen_canvas.SetImage(image.convert('RGB'), 0, 0)
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    foo = input("")

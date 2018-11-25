#
# Office hockey clock
#
import RPi.GPIO as GPIO
import time
import datetime
import colorsys
from dateutil import tz
from datetime import timedelta

from ics import Calendar, Event
from urllib.request import urlopen,Request
from urllib.parse import urlencode

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image

GPIO.setmode(GPIO.BOARD)
PIN_DATA  = 5
PIN_LATCH = 7
PIN_CLOCK = 3

PIN_DATA  = 21
PIN_LATCH = 23
PIN_CLOCK = 19
PIN_ENA   = 24

GPIO.setup(PIN_DATA,  GPIO.OUT)
GPIO.setup(PIN_LATCH, GPIO.OUT)
GPIO.setup(PIN_CLOCK, GPIO.OUT)
GPIO.setup(PIN_ENA,   GPIO.OUT)

GPIO.output(PIN_DATA, 0)
GPIO.output(PIN_CLOCK, 0)
GPIO.output(PIN_LATCH, 0)
GPIO.output(PIN_ENA, 0)

#matrix = RGBMatrix()

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'
options.gpio_slowdown = 2

matrix = RGBMatrix(options = options)


rithockey = Image.open("rithockey.png")
image       = Image.new('RGBA', (matrix.width, matrix.height))
image.paste(rithockey, (0,0), mask=rithockey)


# Make image fit our screen.
#image.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)

#matrix.SetImage(image.convert('RGB'))

symbols = {
    #   _7_
    # 2|   |6
    #   _1_
    # 3|   |5
    #   _4_
    #    0,1,2,3,4,5,6,7
    " ":[0,0,0,0,0,0,0,0],
    "'":[1,0,0,0,0,0,0,0],
    "-":[0,1,0,0,0,0,0,0],
    ".":[0,0,0,1,0,0,0,0],
    "0":[0,0,1,1,1,1,1,1],
    "1":[0,0,0,0,0,1,1,0],
    "2":[0,1,0,1,1,0,1,1],
    "3":[0,1,0,0,1,1,1,1],
    "4":[0,1,1,0,0,1,1,0],
    "5":[0,1,1,0,1,1,0,1],
    "6":[0,1,1,1,1,1,0,1],
    "7":[0,0,0,0,0,1,1,1],
    "8":[0,1,1,1,1,1,1,1],
    "9":[0,1,1,0,1,1,1,1],
    ":":[0,0,1,1,0,0,0,0],
    "=":[0,1,0,0,1,0,0,0],
    "A":[0,1,1,1,0,1,1,1],
    "C":[0,0,1,1,1,0,0,1],
    "E":[0,1,1,1,1,0,0,1],
    "F":[0,1,1,1,0,0,0,1],
    "H":[0,1,1,1,0,1,1,0],
    "P":[0,1,1,1,0,0,1,1],
    "_":[0,0,0,0,1,0,0,0],
    "b":[0,1,1,1,1,1,0,0],
    "d":[0,1,0,1,1,1,1,0],
    "h":[0,1,1,1,0,1,0,0],
    "o":[0,1,0,1,1,1,0,0],
    "r":[0,1,0,1,0,0,0,0],
    "u":[0,0,0,1,1,1,0,0],
    "y":[0,1,1,0,1,1,1,0],
    "|":[0,0,1,1,0,0,0,0],

}
keys = sorted(symbols.keys())
def shiftout(byte):
    for x in range(0,8):
        #print str(byte[x])+"\n"
        GPIO.output(PIN_DATA, byte[x]&1)
        time.sleep(0.00000001)
        GPIO.output(PIN_CLOCK, 1)
        time.sleep(0.00000001)
        GPIO.output(PIN_DATA, 0)
        GPIO.output(PIN_CLOCK, 0)
        time.sleep(0.00000001)
        #print "\n";

offscreen_canvas = matrix.CreateFrameCanvas()
font = graphics.Font()
font.LoadFont("rpi-rgb-led-matrix/fonts/6x9.bdf")
smfont = graphics.Font()
smfont.LoadFont("rpi-rgb-led-matrix/fonts/tom-thumb.bdf")
medfont = graphics.Font()
medfont.LoadFont("rpi-rgb-led-matrix/fonts/6x13.bdf")
tightfont = graphics.Font()
tightfont.LoadFont("rpi-rgb-led-matrix/fonts/clR6x12.bdf")
largefont = graphics.Font()
largefont.LoadFont("rpi-rgb-led-matrix/fonts/10x20.bdf")
white = graphics.Color(200, 200, 200)
yellow = graphics.Color(255, 255, 0)
orange = graphics.Color(255, 165, 0)

def getCalendar( url ):
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = { 'User-Agent' : user_agent }
    values = {}

    data = urlencode(values).encode('utf-8')

    req = Request(url, data, headers)
    response = urlopen(req)
    c = Calendar(response.read().decode('iso-8859-1'))
    earliest = c.events[0]
    for e in c.events:
        if e.begin.astimezone(tz.tzlocal()).isoformat() < datetime.datetime.now().isoformat():
            break
        if earliest.begin > e.begin:
            earliest = e
    return earliest


def updateCalendars():
    print("Updating calendars...")
    nextMensGame = getCalendar( "http://www.ritathletics.com/calendar.ashx/calendar.ics?sport_id=9")
    nextWomensGame = getCalendar( "http://www.ritathletics.com/calendar.ashx/calendar.ics?sport_id=10")
    return nextMensGame, nextWomensGame

nextMensGame, nextWomensGame = updateCalendars()
lastCalUpdate = time.time() 

def doGame( nextGame, duration ):
    global offscreen_canvas, graphics
    posLoc = posNG = offscreen_canvas.width
    t_end = time.time() + duration
    now = time.time()
    btime = time.time() + 2
    blink = 0

    while now < t_end:
        now = time.time()
        if btime < now:
            blink = not blink
            btime = now+2

        offscreen_canvas.Clear()
        if nextGame.name.find("Women") != -1:
            lenT = graphics.DrawText(offscreen_canvas, tightfont, 13, 8, orange, "Next Women's Game")
        else:
            lenT = graphics.DrawText(offscreen_canvas, tightfont, 19, 8, orange, "Next Men's Game")
        
        if nextGame.location.find("Polisseni") != -1:
            len = graphics.DrawText(offscreen_canvas, tightfont, posLoc, 31, orange, "HOME vs"+ nextGame.name.split(" vs ",1)[1].replace("  "," "))
        else:
            len = graphics.DrawText(offscreen_canvas, tightfont, posLoc, 31, white, "Away vs"+nextGame.name.split(" at ",1)[1].replace("  "," "))
        posLoc -= 1.5
        if (posLoc + len < 0):
            if time.time() > t_end:
                break
            posLoc = offscreen_canvas.width
        
        len = graphics.DrawText(offscreen_canvas, tightfont, 0, 18, white, nextGame.begin.astimezone(tz.tzlocal()).strftime("%A")+"{d:%l}:{d.minute:02}{d:%p}".format(d=nextGame.begin.astimezone(tz.tzlocal())))

        time.sleep(0.05)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

        until = nextGame.begin.astimezone(tz.tzlocal()).replace(tzinfo=tz.tzlocal()) - datetime.datetime.now().replace(tzinfo=tz.tzlocal())
        if until.days > 9:
            shiftout(symbols[str(" ")])
            shiftout(symbols[str("d")])
            shiftout(symbols[str(until.days%10)])
            shiftout(symbols[str(until.days//10)])
        elif until.days > 0:
            #print(until.seconds//3600)
            #print((until.seconds//60)%60)
            if blink:
                shiftout(symbols[str(" ")])
                shiftout(symbols[str("h")])
                shiftout(symbols[str((until.seconds//3600)%10)])
                shiftout(symbols[str((until.seconds//3600)//10)])
            else:
                shiftout(symbols[str(" ")])
                shiftout(symbols[str("d")])
                #if until.seconds//3600 > 12 and until.days < 9:
                #    shiftout(symbols[str(until.days+1)])
                #else:
                shiftout(symbols[str(until.days)])
                shiftout(symbols[str("-")])
        else:
            h = until.seconds//3600
            m = (until.seconds%3600)//60
            shiftout(symbols[str(m%10)])
            shiftout(symbols[str(m//10)])
            shiftout(symbols[str(h%10)])
            if h > 9:
                shiftout(symbols[str(h//10)])
            else:
                shiftout(symbols[str("-")])

        GPIO.output(PIN_LATCH, 1)
        time.sleep(0.00000001)
        GPIO.output(PIN_LATCH, 0)
        time.sleep(.01)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


def doClock( duration ):
    global offscreen_canvas, graphics
    i=0;
    t_end = time.time() + duration
    while time.time() < t_end:
        color = colorsys.hsv_to_rgb(i/1000, 1.0, 1.0)
        #print(color)
        offscreen_canvas.Clear()
        len = graphics.DrawText(offscreen_canvas, largefont, 4, 17, graphics.Color(color[0]*255, color[1]*255, color[2]*255), "Current Time")
        len = graphics.DrawText(offscreen_canvas, tightfont, 5, 29, white, custom_strftime("%a, %b {S}, %Y", datetime.datetime.now()))
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        now = datetime.datetime.now()
        shiftout(symbols[str(now.minute%10)])
        shiftout(symbols[str(now.minute//10)])
        shiftout(symbols[str((now.hour%12)%10)])
        if (now.hour%12)//10 > 0:
            shiftout(symbols[str((now.hour%12)//10)])
        else:
            shiftout(symbols[" "])
        GPIO.output(PIN_LATCH, 1)
        time.sleep(0.00000001)
        GPIO.output(PIN_LATCH, 0)
        time.sleep(.1);
        i+=10

while True:
    matrix.SetImage(image.convert('RGB'), 0, 0)
    time.sleep(10)
    doClock(5)
    doGame(nextMensGame, 15)
    doGame(nextWomensGame, 15)
    if(lastCalUpdate + 60*60 < time.time()):
        nextMensGame, nextWomensGame = updateCalendars()
        lastCalUpdate = time.time() 
	
GPIO.cleanup() 

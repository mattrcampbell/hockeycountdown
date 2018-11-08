#
# Office hockey clock
#
import RPi.GPIO as GPIO
import time
import datetime
from dateutil import tz
from datetime import timedelta

from ics import Calendar, Event
from urllib.request import urlopen,Request
from urllib.parse import urlencode

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

GPIO.setmode(GPIO.BOARD)
PIN_DATA  = 5
PIN_LATCH = 7
PIN_CLOCK = 3

PIN_DATA  = 21
PIN_LATCH = 23
PIN_CLOCK = 19

GPIO.setup(PIN_DATA,  GPIO.OUT)
GPIO.setup(PIN_LATCH, GPIO.OUT)
GPIO.setup(PIN_CLOCK, GPIO.OUT)

GPIO.output(PIN_DATA, 0)
GPIO.output(PIN_CLOCK, 0)
GPIO.output(PIN_LATCH, 0)

#matrix = RGBMatrix()

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'  # If you have an Adafruit HAT: 'adafruit-hat'
options.gpio_slowdown = 2

matrix = RGBMatrix(options = options)


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

    while time.time() < t_end:
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
        if until.days > 0:
            #print(until.seconds//3600)
            #print((until.seconds//60)%60)
            shiftout(symbols[str("d")])
            if until.seconds//3600 > 12:
                shiftout(symbols[str(until.days+1)])
            else:
                shiftout(symbols[str(until.days)])
            shiftout(symbols[str("-")])
            shiftout(symbols[str(" ")])
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
        time.sleep(.01);


def doClock( duration ):
    i=0;
    t_end = time.time() + duration
    while time.time() < t_end:
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
        i+=1

while True:
    offscreen_canvas.Clear()
    len = graphics.DrawText(offscreen_canvas, tightfont, 4, 10, white, "Time")
    len = graphics.DrawText(offscreen_canvas, tightfont, 7, 20, white, "Now")
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    #doClock(5)
    doGame(nextMensGame, 15)
    doGame(nextWomensGame, 15)
    if(lastCalUpdate + 60*60 < time.time()):
        nextMensGame, nextWomensGame = updateCalendars()
        lastCalUpdate = time.time() 
	
GPIO.cleanup() 

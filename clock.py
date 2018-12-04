#
# Office hockey clock
#
import RPi.GPIO as GPIO
import time
import datetime
import colorsys
import os
import json
import config
from dateutil import tz
from datetime import timedelta

from ics import Calendar, Event
from urllib.request import urlopen,Request
from urllib.parse import urlencode

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from movingpanel import MovingPanel
from movingpanel import Direction

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
options.hardware_mapping = 'adafruit-hat-pwm'
options.gpio_slowdown = 2

matrix = RGBMatrix(options = options)


image = Image.open("tigerhead.png")
tigerhead = Image.new('RGBA', (matrix.width, matrix.height))
tigerhead.paste(image, (0,0), mask=image)

image = Image.open("rithockey.png")
rithockey = Image.new('RGBA', (matrix.width, matrix.height))
rithockey.paste(image, (0,0), mask=image)

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
smfont    =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/5x8-KOI8-R.pil")
medfont   =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/9x15B.pil")
tightfont =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/clB6x12.pil")
largefont =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/10x20.pil")

white  = (200, 200, 200)
yellow = (255, 255, 0)
orange = (255, 165, 0)

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
    global offscreen_canvas, graphics, matrix
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
        image = Image.new('RGBA', (matrix.width, matrix.height))
        imageDraw = ImageDraw.Draw(image)
        if nextGame.name.find("Women") != -1:
            imageDraw.text((36, -2), "Women's Hockey", font=tightfont, fill=orange)
        else:
            imageDraw.text((36, -2), "Men's Hockey", font=tightfont, fill=orange)
        
        len = imageDraw.text((36, 9), nextGame.begin.astimezone(tz.tzlocal()).strftime("%A")+"{d:%l}:{d.minute:02}{d:%p}".format(d=nextGame.begin.astimezone(tz.tzlocal())), font=smfont, fill=white)

        if nextGame.location.find("Polisseni") != -1:
            text = "HOME vs"+ nextGame.name.split(" vs ",1)[1].replace("  "," ")
            imageDraw.text((posLoc, 16), text, font=medfont, fill=orange)
        else:
            text = "Away vs"+nextGame.name.split(" at ",1)[1].replace("  "," ")
            imageDraw.text((posLoc, 16), text, font=medfont, fill=white)
        len = imageDraw.textsize(text, font=medfont)[0]
        posLoc -= 1.5
        if (posLoc + len < 0):
            #if time.time() > t_end:
            #    break
            #posLoc = image.width
            break

        image.paste(tigerhead, (0, 0), tigerhead)
        offscreen_canvas.SetImage(image.convert('RGB'), 0, 0)
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
                if (until.seconds//3600)//10 > 9:
                    shiftout(symbols[str((until.seconds//3600)//10)])
                else:
                    shiftout(symbols[str(" ")])
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


def doClock( duration, temp, weather, icon ):
    global offscreen_canvas, graphics
    i=0;
    t_end = time.time() + duration
    while time.time() < t_end:
        #color = colorsys.hsv_to_rgb(i/1000, 1.0, 1.0)
        #print(color)
        offscreen_canvas.Clear()
        image = Image.new('RGBA', (matrix.width, matrix.height))
        imageDraw = ImageDraw.Draw(image)
        image.paste(icon, (0,0) )
        i = .7-((temp/100)*.7)
        color = colorsys.hsv_to_rgb(i, 1.0, 1.0)
        imageDraw.text( (33, 0), str(temp), font=largefont, fill=(int(color[0]*255), int(color[1]*255), int(color[2]*255)))
        imageDraw.arc( (55,0,59,4),0,360,fill=(int(color[0]*255), int(color[1]*255), int(color[2]*255)))
        weather = "Partly Cloudy"
        f = largefont
        xo = 0
        len = imageDraw.textsize(weather, font=f)[0]
        if len > 128-62:
            f=tightfont
            xo = 7
            len = imageDraw.textsize(weather, font=f)[0]
            if len > 128-62:
                f=smfont
                xo = 9
        imageDraw.text( (62, xo), weather, font=f, fill=(int(color[0]*255), int(color[1]*255), int(color[2]*255)))
        imageDraw.text( (33, 20), custom_strftime("%a, %b {S}", datetime.datetime.now()), font=tightfont, fill=white)
        offscreen_canvas.SetImage(image.convert('RGB'), 0, 0)
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

def doTransition():
    global offscreen_canvas, graphics, matrix

    image = Image.new('RGBA', (matrix.width, matrix.height))
    imageDraw = ImageDraw.Draw(image)
    image.paste(tigerhead, (0, 0), tigerhead)
    for i in range(matrix.width):
        offscreen_canvas.Clear()
        offscreen_canvas.SetImage(image.convert('RGB'), i, 0)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(.001);
    for i in range(tigerhead.width):
        offscreen_canvas.Clear()
        offscreen_canvas.SetImage(image.convert('RGB'), i-tigerhead.width, 0)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(.001);

weatherTime = 0
try:
    while True:
        doGame(nextMensGame, 15)
        doGame(nextWomensGame, 15)
        currentTime = time.time()
        if(lastCalUpdate + 60*60 < time.time()):
            nextMensGame, nextWomensGame = updateCalendars()
            lastCalUpdate = currentTime 

        if weatherTime+600 < currentTime:
            try:
                print("Get weather...\n");
                weatherTime = currentTime
                f = urlopen('http://api.wunderground.com/api/'+config.wapi+'/geolookup/conditions/q/NY/Rochester.json')
                json_string = f.read().decode('utf-8')
                parsed_json = json.loads(json_string)
                location = parsed_json['location']['city']
                tempf = int(round(parsed_json['current_observation']['temp_f']))
                weather = parsed_json['current_observation']['weather']
                icon = parsed_json['current_observation']['icon']
                iconImg = Image.open("icons/32x32/"+icon+".png")
                print ("Current temperature in %s is: %s" % (location, tempf))
                f.close()
            except:
                print ("Can't get weather data\n")
        
        doClock(5, tempf, weather, iconImg)

finally:
    GPIO.cleanup() 

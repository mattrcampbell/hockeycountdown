#
# Office hockey clock
#
import sys,traceback
import RPi.GPIO as GPIO
import time
import datetime
import colorsys
import os
import json
import config
import re
import statsapi
from pytz import timezone
from snow import Snow
from rain import Rain

from io import BytesIO

from dateutil import tz
from datetime import timedelta

from icalendar import Calendar, Event
from urllib.request import urlopen,Request
from urllib.parse import urlencode

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps    


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

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = 'adafruit-hat-pwm'
options.gpio_slowdown = 2

matrix = RGBMatrix(options = options)

weather = None #Snow(matrix.width, matrix.height)
with open('icons.json') as f:
    iconmap = json.load(f)

image = Image.open("sox.png")
sox = Image.new('RGBA', (matrix.width, matrix.height))
sox.paste(image, (0,0), mask=image)

image = Image.open("tigerhead.png")
tigerhead = Image.new('RGBA', (matrix.width, matrix.height))
tigerhead.paste(image, (0,0), mask=image)

image = Image.open("barons.png")
barons = Image.new('RGBA', (matrix.width, matrix.height))
barons.paste(image, (0,0), mask=image)

image = Image.open("blues.png")
blues = Image.new('RGBA', (matrix.width, matrix.height))
blues.paste(image, (0,0), mask=image)

image = Image.open("rithockey.png")
rithockey = Image.new('RGBA', (matrix.width, matrix.height))
rithockey.paste(image, (0,0), mask=image)

image = Image.open("cougars.png")
cougars = Image.new('RGBA', (matrix.width, matrix.height))
cougars.paste(image, (0,0), mask=image)

calendars = [ 
{ "name":"Cougars", "url":"http://srv1-advancedview.rschooltoday.com/public/conference/ical/u/0072159751ae796db2fa55b70a1578c3", "icon":cougars, "pattern":None, "exclude":"Date Changed to"},
{ "name":"Red Sox", "url":"http://api.calreply.net/webcal/24b4e4c1-ac1b-4c0f-ac16-f0f730736b56", "icon":sox, "pattern":None, "exclude":None},
{ "name":"Men's Hockey", "url":"http://www.ritathletics.com/calendar.ashx/calendar.ics?sport_id=9", "icon":tigerhead, "pattern":None, "exclude":None},
{ "name":"Women's Hockey", "url":"http://www.ritathletics.com/calendar.ashx/calendar.ics?sport_id=10", "icon":tigerhead, "pattern":None, "exclude":None},
{ "name":"Barons", "url":"http://sectionvhockey.org/calendar_events/calendar/3095/168976/-1/0/0/none/true.ics?1543938015", "icon":blues, "pattern":"Bighton", "exclude":None},
{ "name":"Blues", "url":"http://my.sportngin.com/ical/my_teams?team_ids[]=2920662", "icon":barons, "pattern":None, "exclude":None}
]


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

def putClock(string):
    #print("Put to clock ["+string+"]\n")
    shiftout(symbols[string[3]])
    shiftout(symbols[string[2]])
    shiftout(symbols[string[1]])
    shiftout(symbols[string[0]])
    GPIO.output(PIN_LATCH, 1)
    time.sleep(0.00000001)
    GPIO.output(PIN_LATCH, 0)

putClock("8888")


offscreen_canvas = matrix.CreateFrameCanvas()
font = graphics.Font()
font.LoadFont("rpi-rgb-led-matrix/fonts/6x9.bdf")
smfont    =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/5x8-KOI8-R.pil")
medfont   =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/9x15B.pil")
tightfont =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/clB6x12.pil")
largefont =  ImageFont.load(os.path.dirname(os.path.realpath(__file__)) + "/fonts/10x20.pil")

white  = (200, 200, 200)
red    = (255, 20, 20)
yellow = (255, 255, 0)
orange = (255, 165, 0)

def oldgetCalendar( url, check = None ):
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = { 'User-Agent' : user_agent }
    values = {}

    data = urlencode(values).encode('utf-8')

    #req = Request(url, data, headers)
    req = Request(url, None, headers)
    response = urlopen(req)
    r = response.read().decode('iso-8859-1')
    r = re.sub(r';X-RICAL-TZSOURCE=TZINFO', '', r, flags=re.DOTALL)
    #print(r)
    c = Calendar(r)
    earliest = None #c.events[0]
    for e in c.events:
        if check is not None and str(e['SUMMARY']).find(check) == -1:
            continue
        if e.begin.astimezone(tz.tzlocal()).isoformat() < datetime.datetime.now().isoformat():
            return earliest
        if earliest is None or earliest.begin > e.begin:
            earliest = e
    return None

def getCalendar( url, check = None, exclude = None ):
    local_tz = timezone('America/New_York')
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = { 'User-Agent' : user_agent }
    values = {}

    data = urlencode(values).encode('utf-8')

    #req = Request(url, data, headers)
    req = Request(url, None, headers)
    response = urlopen(req)
    r = response.read().decode('iso-8859-1')
    r = re.sub(r';X-RICAL-TZSOURCE=TZINFO', '', r, flags=re.DOTALL)
    #print(r)
    c = Calendar.from_ical(r)
    earliest = None #c.events[0]
    for e in c.walk('vevent'):
        if check is not None and str(e['SUMMARY']).find(check) == -1:
            continue

        if exclude is not None and str(e['SUMMARY']).find(exclude) != -1:
            continue

        # Remove things that are not a datetime
        if not isinstance(e['DTSTART'].dt, datetime.datetime):
            print("For some reason it is not a datetime?")
            print(e)
            continue
      
        # Localize if necessary
        if e['DTSTART'].dt.tzinfo is None:
            e['DTSTART'].dt = local_tz.localize(e['DTSTART'].dt)
    
        # Ignore things in the past
        if e['DTSTART'].dt.astimezone(tz.tzlocal()).isoformat() < datetime.datetime.now().isoformat():
            continue

        if earliest is None or earliest['DTSTART'].dt > e['DTSTART'].dt:
            print(e['SUMMARY']);
            print(e['DTSTART'].dt);
            if earliest is not None:
                print(earliest['DTSTART'].dt);
            earliest = e

    if earliest is None:
        return None
    if earliest['DTSTART'].dt.astimezone(tz.tzlocal()).isoformat() < datetime.datetime.now().isoformat():
        print (earliest['DTSTART'].dt.astimezone(tz.tzlocal()).isoformat() )
        print (datetime.datetime.now().isoformat())
        print("BAD")
        return None
    print(earliest)
    return earliest


def updateCalendars():
    global calendars
    print("Updating calendars...")
    for c in calendars:
        print("Updating calendar: "+c["name"])
        c['next'] = getCalendar( c["url"], c["pattern"], c["exclude"])
    

updateCalendars()
lastCalUpdate = time.time() 

def doGame( nextGame, who, icon, duration ):
    global offscreen_canvas, graphics, matrix, weather
    posLoc = posNG = offscreen_canvas.width
    t_end = time.time() + duration
    now = time.time()
    btime = time.time() + 2
    blink = 0

    image = Image.new('RGBA', (matrix.width, matrix.height))
    imageDraw = ImageDraw.Draw(image)
    while now < t_end:
        now = time.time()
        if btime < now:
            blink = not blink
            btime = now+2

        offscreen_canvas.Clear()
        imageDraw.rectangle((0,0,matrix.width, matrix.height), fill=(0,0,0,0))
        imageDraw.text((36, -2), who, font=tightfont, fill=orange)
        until = nextGame['DTSTART'].dt.astimezone(tz.tzlocal()).replace(tzinfo=tz.tzlocal()) - datetime.datetime.now().replace(tzinfo=tz.tzlocal())
       
        if(until.days < 7):
            len = imageDraw.text((36, 9), nextGame['DTSTART'].dt.astimezone(tz.tzlocal()).strftime("%A")+"{d:%l}:{d.minute:02}{d:%p}".format(d=nextGame['DTSTART'].dt.astimezone(tz.tzlocal())), font=smfont, fill=white)
        else:
            len = imageDraw.text((36, 9), nextGame['DTSTART'].dt.astimezone(tz.tzlocal()).strftime("%Y/%m/%d").format(d=nextGame['DTSTART'].dt.astimezone(tz.tzlocal())), font=smfont, fill=white)

        #print(nextGame['SUMMARY'])
        #if who == "Men's Hockey" or who == "Women's Hockey":
        #    if nextGame['LOCATION'].find("Polisseni") != -1:
        #        text = "HOME vs"+ str(nextGame['SUMMARY']).split(" vs ",1)[1].replace("  "," ")
        #        c=orange
        #    else:
        #        text = "Away vs"+str(nextGame['SUMMARY']).split(" at ",1)[1].replace("  "," ")
        #        c=white
        #else:
        #    c=(0,0,255)
        #    text = str(nextGame['SUMMARY'])
        c=(0,0,255)
        text = str(nextGame['SUMMARY'])

        text = re.sub(r'Baseball: .* vs. ', '', text)

        imageDraw.text((posLoc, 16), text, font=medfont, fill=c)
        len = imageDraw.textsize(text, font=medfont)[0]
        posLoc -= 1.5
        if (posLoc + len < 0):
            #if time.time() > t_end:
            #    break
            #posLoc = image.width
            break

        image.paste(icon, (0,0), icon)
        
        if weather is not None:
            weather.update(imageDraw)
        offscreen_canvas.SetImage(image.convert('RGB'), 0, 0)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

        if until.days > 9:
            putClock(str(until.days)+"d ")
        elif until.days > 0:
            #print(until.seconds//3600)
            #print((until.seconds//60)%60)
            if blink:
                h = until.seconds//3600
                if h > 9:
                    putClock(str(h)+"h ")
                else:
                    putClock(" "+str(h)+"h ")
            else:
                putClock("-"+str(until.days)+"d ")
        else:
            h = until.seconds//3600
            m = (until.seconds%3600)//60
            if h > 9:
                putClock(str(h)+str(m).zfill(2))
            else:
                putClock("-"+str(h)+str(m).zfill(2))

        time.sleep(.01)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


def doClock( duration, temp, forecast, icon ):
    global offscreen_canvas, graphics, weather
    i=0;
    t_end = time.time() + duration
    image = Image.new('RGBA', (matrix.width, matrix.height))
    imageDraw = ImageDraw.Draw(image)
    while time.time() < t_end:
        #color = colorsys.hsv_to_rgb(i/1000, 1.0, 1.0)
        #print(color)
        offscreen_canvas.Clear()
        imageDraw.rectangle((0,0,matrix.width, matrix.height), fill=(0,0,0,0))
        if temp is not None and forecast is not None:
            image.paste(icon, (0,0) )
            i = .7-((temp/100)*.7)
            color = colorsys.hsv_to_rgb(i, 1.0, 1.0)
            imageDraw.text( (33, 0), str(temp), font=largefont, fill=(int(color[0]*255), int(color[1]*255), int(color[2]*255)))
            imageDraw.arc( (55,0,59,4),0,360,fill=(int(color[0]*255), int(color[1]*255), int(color[2]*255)))
            #forecast = "Partly Cloudy"
            f = largefont
            xo = 0
            len = imageDraw.textsize(forecast, font=f)[0]
            if len > 128-62:
                f=tightfont
                xo = 7
                len = imageDraw.textsize(forecast, font=f)[0]
                if len > 128-62:
                    f=smfont
                    xo = 9
            imageDraw.text( (62, xo), forecast, font=f, fill=(int(color[0]*255), int(color[1]*255), int(color[2]*255)))
        imageDraw.text( (33, 20), custom_strftime("%a, %b {S}", datetime.datetime.now()), font=tightfont, fill=white)
        
        if weather is not None:
            weather.update(imageDraw)
        offscreen_canvas.SetImage(image.convert('RGB'), 0, 0)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        now = datetime.datetime.now()
        hh = now.hour%12
        if hh == 0:
            hh = 12
        if hh < 10:
            putClock(" "+str(hh)+str(now.minute).zfill(2))
        else:
            putClock(str(hh)+str(now.minute).zfill(2))
        time.sleep(.01);
        i+=10

teamNameCache = {}
def baseballStandings( duration ):
    global offscreen_canvas, graphics, weather, teamNameCache
    r = statsapi.get('standings', {'leagueId':103, 'season':2019})
    standings = ""
    t_end = time.time() + duration
    image = Image.new('RGBA', (matrix.width, matrix.height))
    imageDraw = ImageDraw.Draw(image)
    while time.time() < t_end:
        ypos = 0;
        imageDraw.rectangle((0,0,matrix.width, matrix.height), fill=(0,0,0,0))
        for y in (y for y in r['records'] if y['division']['id']==201):
            for x in y['teamRecords']:
                if x['team']['name'] not in teamNameCache:
                    teamNameCache[x['team']['name']] = statsapi.lookup_team(x['team']['name'])[0]['teamName']#.upper()
                if teamNameCache[x['team']['name']] == "Red Sox":
                    c = red
                else:
                    c = white
                line = "%10s %d %d %s %s\n" % (teamNameCache[x['team']['name']], x['wins'], x['losses'], x['winningPercentage'], x['gamesBack'])
                imageDraw.text( (0, ypos), line, font=smfont, fill=c)
                ypos += 8
        if weather is not None:
            weather.update(imageDraw)
        offscreen_canvas.Clear()
        offscreen_canvas.SetImage(image.convert('RGB'), 0, 0)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        now = datetime.datetime.now()
        hh = now.hour%12
        if hh == 0:
            hh = 12
        if hh < 10:
            putClock(" "+str(hh)+str(now.minute).zfill(2))
        else:
            putClock(str(hh)+str(now.minute).zfill(2))
        time.sleep(.01);


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

def animatedGif(duration, delay, fileName):
    global offscreen_canvas, graphics, matrix
    t_end = time.time() + duration
    im = Image.open(fileName)
    nframe = 0
    while time.time() < t_end:
        try:
            im.seek( nframe )
            nframe += 1
        except:
            nframe = 0
            im.seek( nframe )
        offscreen_canvas.Clear()
        offscreen_canvas.SetImage(im.convert('RGB'), 0, 0)
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(delay);


weatherTime = 0
tempf = None
forecast = None
iconImg = None
# https://gist.github.com/tbranyen/62d974681dea8ee0caa1
try:
    while True:
        baseballStandings(10);
        #animatedGif(3, .1,  'heihei.gif')
        currentTime = time.time()
        if(lastCalUpdate + 60*60 < time.time()):
            updateCalendars()
            lastCalUpdate = currentTime 
        if weatherTime+600 < currentTime:
            try:
                print("Get weather...\n");
                weatherTime = currentTime
                f = urlopen('http://api.openweathermap.org/data/2.5/weather?id=5134086&units=imperial&APPID='+config.owmapi)
                json_string = f.read().decode('utf-8')
                parsed_json = json.loads(json_string)
                print(parsed_json)
                location = parsed_json['name']
                tempf = int(round(parsed_json['main']['temp']))
                forecast = parsed_json['weather'][0]['description'].title()
                #forecast = "Heavy Rain"
                if forecast.upper().find('SNOW') != -1:
                    weather = Snow(matrix.width, matrix.height)
                elif forecast.upper().find('RAIN') != -1:
                    weather = Rain(matrix.width, matrix.height, forecast)
                else:
                    weather = None
                icon = parsed_json['weather'][0]['icon']
                iconfile = iconmap[str(parsed_json['weather'][0]['id'])]['icon']
                print(iconfile)
                iconImg = Image.open("icons/32x32/"+iconfile+".png")
                #iconImg = Image.open("weather-icons/svg/wi-"+iconfile+".png")
                iconImg = ImageOps.solarize(iconImg)
                print ("Current temperature in %s is: %s" % (location, tempf))
                f.close()
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                print ("Can't get weather data\n")
        
        doClock(5, tempf, forecast, iconImg)

        for c in calendars:
            if c['next'] is not None:
                doGame(c['next'], c['name'], c['icon'], 15)

finally:
    GPIO.cleanup() 

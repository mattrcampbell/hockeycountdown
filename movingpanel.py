from PIL import Image
from PIL import ImageDraw
from enum import Enum
import time
import sys

class Direction(Enum):
	LEFT = 1
	RIGHT = 2
	UP = 3
	DOWN = 4

class MovingPanel():
	holding = False
	curX = 0;
	curY = 0;
	lastHold = time.time()
	lastDraw = time.time()
	curPart = 0

	def __init__(self, width, height, direction, fps, hold = [], parts = []):
		self.parts = parts
		self.direction = direction
		self.updateSizes()
		if direction == Direction.LEFT or direction == Direction.RIGHT:
			self.image = Image.new('RGBA', (width*(len(parts)+1), height))
		else:
			self.image = Image.new('RGBA', (width, height*len(parts)+1))
		self.draw = ImageDraw.Draw(self.image)
		self.width = width
		self.height = height
		self.hold = hold
		self.fps = fps
		self.draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

	def updateSizes(self, index = 0, newImage = None):
		if newImage is not None:
			self.parts[index] = newImage
		self.totalWidth = 0
		self.totalHeight = 0
		for i in self.parts:
			if self.direction == Direction.LEFT or self.direction == Direction.RIGHT:
				self.totalWidth += i.width
			else:
				self.totalHeight += i.height

	def update(self):

		currentTime = time.time()
		if self.lastHold < currentTime:
			self.holding = False;

		if not self.holding:
			if self.lastDraw+(self.fps) < currentTime:
				self.lastDraw = currentTime
		
				if self.direction == Direction.LEFT:
					self.curX-=1;
				elif self.direction == Direction.RIGHT:
					self.curX+=1;
				elif self.direction == Direction.UP:
					self.curY-=1;
				elif self.direction == Direction.DOWN:
					self.curY+=1;

				x = self.curX
				y = self.curY
				self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
				for i in self.parts:
					self.image.paste(i, (x,y), i.convert('RGBA'))
					if self.direction == Direction.LEFT or self.direction == Direction.RIGHT:
						x += i.width
					else:
						y += i.height
				self.image.paste(self.parts[0], (x,y), self.parts[0].convert('RGBA'))

				if self.direction == Direction.LEFT or self.direction == Direction.RIGHT:
					if self.curX % self.width == 0:
						self.holding = True;
						self.lastHold = currentTime+self.hold[self.curPart%len(self.parts)] ; 
						self.curPart += 1
				else:
					if self.curY % self.height == 0:
						self.holding = True;
						self.lastHold = currentTime+self.hold[self.curPart%len(self.parts)] ; 
						self.curPart += 1

			if self.direction == Direction.LEFT:
				if self.curX <= -1*self.totalWidth:
					self.curX = 0
					self.curPart = 0
			elif self.direction == Direction.RIGHT:
				if self.curX >= 0:
					self.curX = -1*self.totalWidth
					self.curPart = 0
			elif self.direction == Direction.UP:
				if self.curY <= -1*self.totalHeight:
					self.curY = 0
					self.curPart = 0
			elif self.direction == Direction.DOWN:
				if self.curY >= 0:
					self.curY = -1*self.totalHeight
					self.curPart = 0

	def getImage(self):
		return self.image

	def getDraw(self):
		return self.draw


	

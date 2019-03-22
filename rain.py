import random

class Drop:
    x = 0
    y = 0
    v = 0
    c = (255,255,255)

    def __init__(self, width):
        #self.v = random.uniform(.1,1)
        self.v = 1.5
        self.x = random.randint(0,width)
        self.y = -1*random.randint(0,32)
        r = random.randint(100,150)
        self.c = (r,r,255)
    def update(self):
        self.y=self.y+self.v;
        self.x=self.x+.05
        #self.x=self.x+random.uniform(-.5,.5);

class Rain:
    drops = []
    cnt = 25

    def __init__(self, w, h, rainType):
        self.w = w
        self.h = h
        if rainType.upper().find('LIGHT') != -1:
            print("AAA")
            self.cnt = 25
        elif rainType.upper().find('HEAVY') != -1:
            print("BBB")
            self.cnt = 200

    def update(self, imageDraw):
        #print(str(len(self.drops)))
        for drop in self.drops:
            drop.update()
            imageDraw.line((drop.x, drop.y, drop.x, drop.y+3), fill=drop.c)
            if drop.y > self.h:
                self.drops.remove(drop)
        while len(self.drops) < self.cnt:
            self.drops.append(Drop(self.w))



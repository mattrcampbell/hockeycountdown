import random

class Flake:
    x = 0
    y = 0
    v = 0
    c = (255,255,255)

    def __init__(self, width):
        self.v = random.uniform(.1,1)
        self.x = random.randint(0,width)
        r = random.randint(150,255)
        self.c = (r,r,255)
    def update(self):
        self.y=self.y+self.v;
        self.x=self.x+random.uniform(-.5,.5);

class Snow:
    flakes = []

    def __init__(self, w, h):
        self.w = w
        self.h = h

    def update(self, imageDraw):
        #print(str(len(self.flakes)))
        for flake in self.flakes:
            flake.update()
            imageDraw.point((flake.x, flake.y), fill=flake.c)
            if flake.y > self.h:
                self.flakes.remove(flake)
        if len(self.flakes) < 50:
            self.flakes.append(Flake(self.w))



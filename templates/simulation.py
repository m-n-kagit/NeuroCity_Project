import random
import time
import threading
import pygame
import sys

# ====== Default Timers ======
defaultGreen = {0: 30, 1: 30, 2: 30, 3: 30}
defaultRed = 80
defaultYellow = 5

signals = []
noOfSignals = 4

# Pair: (right,left) and (down,up)
signalPairs = [(0, 2), (1, 3)]
currentPair = 0   # which pair is currently green
currentYellow = 0

speeds = {'car': 4.25, 'bus': 3.8, 'truck': 2.8, 'bike': 5.5}


x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0},
            'down': {0:[], 1:[], 2:[], 'crossed':0},
            'left': {0:[], 1:[], 2:[], 'crossed':0},
            'up': {0:[], 1:[], 2:[], 'crossed':0}}

vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]

stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

counts=0
stoppingGap = 15
movingGap = 15

pygame.init()
simulation = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "./images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

        # Stopping logic
        if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
            prev = vehicles[direction][lane][self.index-1]
            if direction=='right':
                self.stop = prev.stop - prev.image.get_rect().width - stoppingGap
            elif direction=='left':
                self.stop = prev.stop + prev.image.get_rect().width + stoppingGap
            elif direction=='down':
                self.stop = prev.stop - prev.image.get_rect().height - stoppingGap
            elif direction=='up':
                self.stop = prev.stop + prev.image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]

        # Update start coords
        if direction=='right':
            x[direction][lane] -= self.image.get_rect().width + stoppingGap
        elif direction=='left':
            x[direction][lane] += self.image.get_rect().width + stoppingGap
        elif direction=='down':
            y[direction][lane] -= self.image.get_rect().height + stoppingGap
        elif direction=='up':
            y[direction][lane] += self.image.get_rect().height + stoppingGap
        simulation.add(self)

    def move(self):
        pairGreen = signalPairs[currentPair]
        # Check if this direction is currently green
        isGreen = (self.direction_number in pairGreen) and (currentYellow == 0)
        if self.direction == 'right':
            if self.crossed==0 and self.x+self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = 1
            if ((self.x+self.image.get_rect().width<=self.stop or self.crossed or isGreen)
                and (self.index==0 or self.x+self.image.get_rect().width <
                     vehicles[self.direction][self.lane][self.index-1].x - movingGap)):
                self.x += self.speed
        elif self.direction == 'left':
            if self.crossed==0 and self.x < stopLines[self.direction]:
                self.crossed = 1
            if ((self.x>=self.stop or self.crossed or isGreen)
                and (self.index==0 or self.x >
                     vehicles[self.direction][self.lane][self.index-1].x +
                     vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap)):
                self.x -= self.speed
        elif self.direction == 'down':
            if self.crossed==0 and self.y+self.image.get_rect().height > stopLines[self.direction]:
                self.crossed = 1
            if ((self.y+self.image.get_rect().height<=self.stop or self.crossed or isGreen)
                and (self.index==0 or self.y+self.image.get_rect().height <
                     vehicles[self.direction][self.lane][self.index-1].y - movingGap)):
                self.y += self.speed
        elif self.direction == 'up':
            if self.crossed==0 and self.y < stopLines[self.direction]:
                self.crossed = 1
            if ((self.y>=self.stop or self.crossed or isGreen)
                and (self.index==0 or self.y >
                     vehicles[self.direction][self.lane][self.index-1].y +
                     vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap)):
                self.y -= self.speed

def initialize():
    for i in range(noOfSignals):
        signals.append(TrafficSignal(defaultRed, defaultYellow, defaultGreen[i]))
    repeatPairs()

def repeatPairs():
    global currentPair, currentYellow
    while True:
        # Green phase for both signals in the current pair
        for i in signalPairs[currentPair]:
            signals[i].green = defaultGreen[i]
        while signals[signalPairs[currentPair][0]].green > 0:
            updateValues()
            time.sleep(1)

        currentYellow = 1
        for i in signalPairs[currentPair]:
            for lane in range(3):
                for vehicle in vehicles[directionNumbers[i]][lane]:
                    vehicle.stop = defaultStop[directionNumbers[i]]
        while signals[signalPairs[currentPair][0]].yellow > 0:
            updateValues()
            time.sleep(1)
        currentYellow = 0

        # Reset timers
        for i in signalPairs[currentPair]:
            signals[i].green = defaultGreen[i]
            signals[i].yellow = defaultYellow
            signals[i].red = defaultRed

        # Next pair
        currentPair = (currentPair + 1) % len(signalPairs)

def updateValues():
    for i in range(noOfSignals):
        if i in signalPairs[currentPair]:
            if currentYellow == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1

def generateVehicles():
    while True:
        vehicle_type = random.randint(0,3)
        lane_number = random.randint(1,2)
        direction_number = random.randint(0,3)
        Vehicle(lane_number, vehicleTypes[vehicle_type],
                direction_number, directionNumbers[direction_number])
        time.sleep(1)

def display_vehicle_count(surface, font, color=(255,255,255)):
    """
    Show the total vehicles currently in each real-world lane
    (Left, Right, Up, Down).
    """
    lines = []
    grand_total = 0

    for approach in ['left', 'right', 'up', 'down']:
        # Sum all three internal lanes for this approach
        count = sum(len(vehicles[approach][lane]) for lane in range(3))
        if(approach=="left"):
            lines.append(f"Right: {count}")
        if(approach=="rigth"):
            lines.append(f"Left: {count}")
        if(approach=="down"):
            lines.append(f"Up: {count}")
        if(approach=="up"):
            lines.append(f"Down: {count}")
        grand_total += count

    lines.append(f"Total vehicles : {grand_total}")

    x, y = 60, 60
    for text in lines:
        img = font.render(text, True, color)
        surface.blit(img, (x, y))
        y += 25


class Main:
    thread1 = threading.Thread(target=initialize)
    thread1.daemon = True
    thread1.start()

    black = (0,0,0)
    white = (255,255,255)
    screenWidth = 1400
    screenHeight = 800
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    pygame.display.set_caption("SIMULATION")
    background = pygame.image.load('images/intersection.png')
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)
    thread2 = threading.Thread(target=generateVehicles)
    thread2.daemon = True
    thread2.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                sys.exit()

        screen.blit(background,(0,0))
        for i in range(noOfSignals):
            if i in signalPairs[currentPair]:
                if currentYellow == 1:
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                signals[i].signalText = signals[i].red if signals[i].red <= 10 else "---"
                screen.blit(redSignal, signalCoods[i])
        if pygame.time.get_ticks() % 2000 < 20:   # roughly every 2 seconds
            counts = {d: sum(len(vehicles[d][lane]) for lane in range(3))
            for d in ['right','left','up','down']}
            print("Current counts:", counts)
        for i in range(noOfSignals):
            timer = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(timer, signalTimerCoods[i])

        for v in simulation:
            screen.blit(v.image, (v.x, v.y))
            v.move()
        display_vehicle_count(screen, font, (255,255,0))  

        pygame.display.update()

# Run
Main()
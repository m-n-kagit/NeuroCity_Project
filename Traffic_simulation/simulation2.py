import random
import time
import threading
import pygame
import cv2
import numpy as np

# ====== Config ======
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
DEFAULT_GREEN = 10.0  # seconds
DEFAULT_YELLOW = 3.0  # seconds
DEFAULT_RED = 10.0  # not actively used, as red duration is implicit
MIN_GREEN = 5.0
MAX_GREEN = 60.0
GREEN_EXTENSION_FACTOR = 2.0  # seconds per waiting vehicle

speeds = {'car': 50, 'bus': 40, 'truck': 35, 'bike': 60}  # pixels per second, adjusted for visibility

x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

vehicles = {'right': {0: [], 1: [], 2: []},
            'down': {0: [], 1: [], 2: []},
            'left': {0: [], 1: [], 2: []},
            'up': {0: [], 1: [], 2: []}}

vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}
signalPairs = [(0, 2), (1, 3)]  # Right-Left, Down-Up
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stoppingGap = 25  # increased for better spacing
movingGap = 25

currentPair = 0
currentYellow = False

pygame.init()
simulation = pygame.sprite.Group()

# ====== Traffic Signal ======
class TrafficSignal:
    def __init__(self):
        self.state = 'red'
        self.timer = 0.0  # current remaining time in seconds

# ====== Vehicle ======
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
        path = f"./images/{direction}/{vehicleClass}.png"
        self.image = pygame.image.load(path)

        # Set stop position behind previous vehicle
        if self.index > 0:
            prev = vehicles[direction][lane][self.index - 1]
            if prev.crossed == 0:
                if direction == 'right':
                    self.stop = prev.stop - prev.image.get_rect().width - stoppingGap
                elif direction == 'left':
                    self.stop = prev.stop + prev.image.get_rect().width + stoppingGap
                elif direction == 'down':
                    self.stop = prev.stop - prev.image.get_rect().height - stoppingGap
                elif direction == 'up':
                    self.stop = prev.stop + prev.image.get_rect().height + stoppingGap
            else:
                self.stop = defaultStop[direction]
        else:
            self.stop = defaultStop[direction]

        # Update starting position for next vehicle
        if direction == 'right':
            x[direction][lane] -= self.image.get_rect().width + stoppingGap
        elif direction == 'left':
            x[direction][lane] += self.image.get_rect().width + stoppingGap
        elif direction == 'down':
            y[direction][lane] -= self.image.get_rect().height + stoppingGap
        elif direction == 'up':
            y[direction][lane] += self.image.get_rect().height + stoppingGap
        simulation.add(self)

    def move(self, dt):
        signal = signals[self.direction_number]
        can_proceed = (signal.state != 'red')

        # Determine if crossed stop line
        rect = self.image.get_rect()
        if self.direction == 'right' and self.crossed == 0 and self.x + rect.width > stopLines[self.direction]:
            self.crossed = 1
        elif self.direction == 'left' and self.crossed == 0 and self.x < stopLines[self.direction]:
            self.crossed = 1
        elif self.direction == 'down' and self.crossed == 0 and self.y + rect.height > stopLines[self.direction]:
            self.crossed = 1
        elif self.direction == 'up' and self.crossed == 0 and self.y < stopLines[self.direction]:
            self.crossed = 1

        # Move vehicle respecting stop line, previous vehicle, and signal
        move_allowed = False
        if self.direction == 'right':
            if (self.x + rect.width <= self.stop or self.crossed or can_proceed) and \
               (self.index == 0 or self.x + rect.width < (vehicles[self.direction][self.lane][self.index - 1].x - movingGap)):
                self.x += self.speed * dt
                move_allowed = True
        elif self.direction == 'left':
            if (self.x >= self.stop or self.crossed or can_proceed) and \
               (self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().width + movingGap)):
                self.x -= self.speed * dt
                move_allowed = True
        elif self.direction == 'down':
            if (self.y + rect.height <= self.stop or self.crossed or can_proceed) and \
               (self.index == 0 or self.y + rect.height < (vehicles[self.direction][self.lane][self.index - 1].y - movingGap)):
                self.y += self.speed * dt
                move_allowed = True
        elif self.direction == 'up':
            if (self.y >= self.stop or self.crossed or can_proceed) and \
               (self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().height + movingGap)):
                self.y -= self.speed * dt
                move_allowed = True

        # Check if out of screen and remove if so
        if move_allowed and self.is_out_of_screen():
            self.remove()

    def is_out_of_screen(self):
        rect = self.image.get_rect()
        if self.direction == 'right' and self.x > SCREEN_WIDTH:
            return True
        elif self.direction == 'left' and self.x + rect.width < 0:
            return True
        elif self.direction == 'down' and self.y > SCREEN_HEIGHT:
            return True
        elif self.direction == 'up' and self.y + rect.height < 0:
            return True
        return False

    def remove(self):
        simulation.remove(self)
        idx = vehicles[self.direction][self.lane].index(self)
        del vehicles[self.direction][self.lane][idx]
        # Update indices of remaining vehicles in the lane
        for i in range(idx, len(vehicles[self.direction][self.lane])):
            vehicles[self.direction][self.lane][i].index = i

# ====== Initialize signals ======
signals = [TrafficSignal() for _ in range(4)]
for i in signalPairs[currentPair]:
    signals[i].state = 'green'
    signals[i].timer = DEFAULT_GREEN

# ====== Helper Functions ======
def get_waiting_count(pair_index):
    dirs = [directionNumbers[i] for i in signalPairs[pair_index]]
    return sum(1 for d in dirs for l in range(3) for v in vehicles[d][l] if v.crossed == 0)

# ====== Vehicle Generator Thread ======
def generateVehicles():
    while True:
        v_type = random.randint(0, 3)
        lane = random.randint(0, 2)
        dir_num = random.randint(0, 3)
        Vehicle(lane, vehicleTypes[v_type], dir_num, directionNumbers[dir_num])
        time.sleep(1)

threading.Thread(target=generateVehicles, daemon=True).start()

# ====== Signal Update ======
def updateSignals(dt):
    global currentPair, currentYellow
    pair = signalPairs[currentPair]
    for i in pair:
        signals[i].timer -= dt
    if not currentYellow:
        if max(signals[i].timer for i in pair) <= 0:  # Use max to sync if slight diff
            currentYellow = True
            for j in pair:
                signals[j].state = 'yellow'
                signals[j].timer = DEFAULT_YELLOW
    else:
        if max(signals[i].timer for i in pair) <= 0:
            for j in pair:
                signals[j].state = 'red'
                signals[j].timer = 0.0
            currentPair = (currentPair + 1) % len(signalPairs)
            waiting = get_waiting_count(currentPair)
            green_time = max(MIN_GREEN, min(MAX_GREEN, DEFAULT_GREEN + waiting * GREEN_EXTENSION_FACTOR))
            for k in signalPairs[currentPair]:
                signals[k].state = 'green'
                signals[k].timer = green_time
            currentYellow = False

# ====== Vehicle Count Display ======
def display_vehicle_count(surface, font, color=(255, 255, 255)):
    lines = []
    total = 0
    for dir in ['left', 'right', 'up', 'down']:
        count = sum(len(vehicles[dir][lane]) for lane in range(3))
        lines.append(f"{dir.capitalize()}: {count}")
        total += count
    lines.append(f"Total: {total}")
    x0, y0 = 60, 60
    for text in lines:
        surface.blit(font.render(text, True, color), (x0, y0))
        y0 += 25

# ====== Main Simulation Loop ======
def run_simulation_loop():
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background = pygame.image.load('images/intersection.png')
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    prev_time = time.time()
    while True:
        now = time.time()
        dt = now - prev_time
        prev_time = now

        updateSignals(dt)
        for v in list(simulation):
            v.move(dt)

        screen.blit(background, (0, 0))
        for i, sig in enumerate(signals):
            if sig.state == 'green':
                screen.blit(greenSignal, signalCoods[i])
            elif sig.state == 'yellow':
                screen.blit(yellowSignal, signalCoods[i])
            else:
                screen.blit(redSignal, signalCoods[i])
        for v in simulation:
            screen.blit(v.image, (v.x, v.y))
        display_vehicle_count(screen, font)

        frame = pygame.surfarray.array3d(screen)
        frame = np.rot90(frame, 3)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.016)  # ~60 fps

# ====== Flask generator ======
def generate_simulation_frames():
    for f in run_simulation_loop():
        yield f
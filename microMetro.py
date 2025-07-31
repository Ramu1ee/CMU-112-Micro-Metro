#Game inspired by Mini Metro

from cmu_graphics import *
import random
from collections import deque

#Gemini AI designed this breadth first search function to find a transfer path if line does not reach target
#Also imported deque
def findPathBFS(startStation, destinationShape):
    queue = deque([(startStation, [startStation])])
    visited = {startStation}

    if startStation.shape == destinationShape:
        return [startStation]

    while queue:
        currentHeading, path = queue.popleft()

        # Find adjacent stations to currentHeading
        neighbors = set()
        for line in currentHeading.lines:
            try:
                idx = line.stations.index(currentHeading)
                if idx > 0:
                    neighbors.add(line.stations[idx - 1])
                if idx < len(line.stations) - 1:
                    neighbors.add(line.stations[idx + 1])
            except ValueError:
                continue
        
        for neighbor in neighbors:
            if neighbor not in visited:
                new_path = path + [neighbor]
                if neighbor.shape == destinationShape:
                    return new_path  # Found the shortest path
                
                visited.add(neighbor)
                queue.append((neighbor, new_path))
    
    return None  # No path found

def findTransfer(startStation, destinationShape):
    path = findPathBFS(startStation, destinationShape)
    #Return list of stations to pass through
    if not path or len(path) < 3: #No transfer needed, curr or next station is destination
        return None
    currentLines = set(path[0].lines) & set(path[1].lines) #Current possible lines
    #Iterate through the path returned to find whether transfer is need
    for i in range(1, len(path) - 1):
        currentHeading = path[i]
        nextHeading = path[i+1]
        nextLines = set(currentHeading.lines) & set(nextHeading.lines) #Possible lines afterwards
        if not currentLines & nextLines: #No single line possible
            return currentHeading
        currentLines = currentLines & nextLines
    #No transfer needed
    return None


class Station:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.passengers = []
        self.lines = []
        self.radius = 20

    def draw(self):
        #Draw the station
        if self.shape == 'circle':
            drawCircle(self.x, self.y, self.radius, fill='white', border='black', borderWidth=3)
        elif self.shape == 'square':
            drawRegularPolygon(self.x, self.y, self.radius + 5, 4, fill='white', border='black', borderWidth=3, rotateAngle=45)
        elif self.shape == 'triangle':
            drawRegularPolygon(self.x, self.y, self.radius + 5, 3, fill='white', border='black', borderWidth=3)
        elif self.shape == 'diamond':
            drawRegularPolygon(self.x, self.y, self.radius + 5, 4, fill='white', border='black', borderWidth=3)
        elif self.shape == 'pentagon':
            drawRegularPolygon(self.x, self.y, self.radius + 5, 5, fill='white', border='black', borderWidth=3)

        #Draw passengers waiting at station
        for i, passenger in enumerate(self.passengers):
            posX = self.x - 20 + (i % 5) * 10
            posY = self.y + 30 + (i // 5) * 10
            if passenger.destinationShape == 'circle':
                drawCircle(posX, posY, 4.5, fill='Gray')
            elif passenger.destinationShape == 'square':
                drawRegularPolygon(posX, posY, 6, 4, fill='Gray', rotateAngle=45)
            elif passenger.destinationShape == 'triangle':
                drawRegularPolygon(posX, posY+1, 6, 3, fill='Gray')
            elif passenger.destinationShape == 'diamond':
                drawRegularPolygon(posX, posY, 6, 4, fill='Gray')
            elif passenger.destinationShape == 'pentagon':
                drawRegularPolygon(posX, posY, 5, 5, fill='Gray')

class Passenger:
    #Passenger shape is determined by the destination
    def __init__(self, destinationShape):
        self.destinationShape = destinationShape
        self.transferStation = None  #Station where passenger should transfer

class Line:
    def __init__(self, color):
        self.stations = []
        self.color = color
        self.trains = []

    def linkStation(self, station): #Create a line
        if station not in self.stations: #You cant add the same station twice for a line
            self.stations.append(station) #Adds station to line
            station.lines.append(self) #Adds line to station
            #Condition for train existing
            if len(self.stations) == 2:
                self.trains.append(Train(self, 0))

    def extendLine(self, newStation, endStation): #Extend a line
        if newStation in self.stations or endStation not in self.getEndpoints(): #Wrong conditions
            return
        if self.stations[0] == endStation: #Beginning of line
            self.stations.insert(0, newStation)
            for train in self.trains: #Adjust relative train position
                train.currentIndex += 1
                train.targetIndex += 1
        elif self.stations[-1] == endStation: #End of line
            self.stations.append(newStation)
        newStation.lines.append(self)

    def getEndpoints(self):
        return [self.stations[0], self.stations[-1]]

    #Line drawing handled in redrawAll
    def draw(self, app):
        for train in self.trains:
            train.draw(app)

class Train:
    def __init__(self, line, startIndex):
        self.line = line
        self.currentIndex = startIndex #Station train is from
        self.passengers = []
        self.capacity = 6
        self.x, self.y = self.line.stations[startIndex].x, self.line.stations[startIndex].y
        self.targetIndex = startIndex+1 % len(self.line.stations) #Wrap around
        self.speed = 1.5
        self.direction = 1
        self.waitTimer = 0 #For stopping at stations

    def move(self):
        if self.waitTimer > 0:
            self.waitTimer -= 1
            return 0
        if len(self.line.stations) < 2:
            return 0
    
        targetStation = self.line.stations[self.targetIndex]
        dx = targetStation.x - self.x
        dy = targetStation.y - self.y
        distance = (dx**2 + dy**2)**0.5
        if distance < self.speed: #Arrived, snap to target
            self.x, self.y = targetStation.x, targetStation.y
            self.currentIndex = self.targetIndex
            deliveredCount = self.handlePassengers()
            #Flip directions at ends
            if self.targetIndex == len(self.line.stations) - 1:
                self.direction = -1
            elif self.targetIndex == 0:
                self.direction = 1
            self.targetIndex += self.direction
            self.waitTimer = 60 #1 second
            return deliveredCount
        else: #Move
            self.x += (self.speed * dx) / distance
            self.y += (self.speed * dy) / distance
            return 0

    #Drop and take passengers
    def handlePassengers(self):
        deliveredCount = 0
        currentStation = self.line.stations[self.currentIndex]
        #Drop off passengers at their right shape
        tempPassengers = self.passengers.copy()
        self.passengers.clear()
        for passenger in tempPassengers:
            if passenger.destinationShape != currentStation.shape:
                self.passengers.append(passenger) #If not destination
            else:
                deliveredCount += 1 #Reached! add count
        #Drop off passengers who need to transfer
        transferPassengers = []
        remainingPassengers = []
        for passenger in self.passengers:
            if passenger.transferStation == currentStation:
                transferPassengers.append(passenger)
            else:
                remainingPassengers.append(passenger)
        self.passengers = remainingPassengers
        
        #Add transfer passengers to the station
        for passenger in transferPassengers:
            passenger.transferStation = None
            currentStation.passengers.append(passenger)
        
        #Pick up passengers from the station
        for passenger in currentStation.passengers.copy():
            if len(self.passengers) < self.capacity:
                #Check if destination is directly reachable
                destinationAvailable = any(station.shape == passenger.destinationShape for station in self.line.stations)
                if destinationAvailable:
                    #Direct route - pick up passenger
                    self.passengers.append(passenger)
                    currentStation.passengers.remove(passenger)
                else:
                    #Check if we can find a transfer route
                    transferStation = findTransfer(currentStation, passenger.destinationShape)
                    if transferStation and transferStation in self.line.stations:
                        #Pick up passenger and set their transfer station
                        passenger.transferStation = transferStation
                        self.passengers.append(passenger)
                        currentStation.passengers.remove(passenger)

        return deliveredCount

    def draw(self, app):
        startingIndex = self.targetIndex - self.direction
        if not (0 <= startingIndex < len(self.line.stations)):
            drawRect(self.x - 15, self.y - 7, 30, 14, fill=self.line.color, border='black', borderWidth=2) #Train
            return
    
        #Gemini AI - placing trains on correct track when multiple tracks exists on a segment
        targetStation = self.line.stations[self.targetIndex]
        startingStation = self.line.stations[startingIndex]
        segment = tuple(sorted((startingStation, targetStation), key=id))
        offset_distance = 0
        if hasattr(app, 'segment_map') and segment in app.segment_map:
            shared_lines = app.segment_map[segment]
            n = len(shared_lines)
            if self.line in shared_lines:
                line_index = shared_lines.index(self.line)
                spacing = 8
                offset_distance = (line_index - (n - 1) / 2.0) * spacing
        s_start, s_end = segment[0], segment[1]
        dx = s_end.x - s_start.x
        dy = s_end.y - s_start.y
        dist = (dx**2 + dy**2)**0.5
        draw_x, draw_y = self.x, self.y
        if dist > 0:
            perp_dx = -dy / dist
            perp_dy = dx / dist
            draw_x += offset_distance * perp_dx
            draw_y += offset_distance * perp_dy

        #Draw train and its passengers
        drawRect(draw_x - 15, draw_y - 7, 30, 14, fill=self.line.color, border='black', borderWidth=2)
        for i, p in enumerate(self.passengers):
            px = draw_x - 10 + (i % 3) * 10
            py = draw_y + (i // 3 - 0.5) * 8
            if p.destinationShape == 'circle':
                drawCircle(px, py, 3, fill='white')
            elif p.destinationShape == 'square':
                drawRegularPolygon(px, py, 4, 4, fill='white', rotateAngle=45)
            elif p.destinationShape == 'triangle':
                drawRegularPolygon(px, py, 4, 3, fill='white')
            elif p.destinationShape == 'diamond':
                drawRegularPolygon(px, py, 4, 4, fill='white')
            elif p.destinationShape == 'pentagon':
                drawRegularPolygon(px, py, 4, 5, fill='white')


def onAppStart(app):
    #Themes from GarageBand
    app.startTheme = Sound('sound/Start_theme.mp3')
    app.hongKongTheme = Sound('sound/HongKong.mp3')
    app.tokyoTheme = Sound('sound/Tokyo.mp3')
    app.newYorkTheme = Sound('sound/NewYork.mp3')
    #Royalty-free sound effects, downloaded long ago, forgot link
    app.startSound = Sound('sound/continue.wav')
    app.selectSound = Sound('sound/select.wav')
    app.unselectSound = Sound('sound/unselect.wav')
    app.gameOverSound = Sound('sound/game_over.wav')
    app.connectSound = Sound('sound/connect.wav')
    app.buttonSound = Sound('sound/button.wav')
    app.exitSound = Sound('sound/exit.wav')
    app.playSound = Sound('sound/play.wav')
    app.pauseSound = Sound('sound/pause.wav')
    app.stepsPerSecond = 60
    app.highScore = 0


def start_onScreenActivate(app):
    app.startButtonHover = False
    app.startTheme.play(restart=False, loop=True)

def start_onMouseMove(app, mouseX, mouseY):
    #'Fake' hover effect
    if intersectionRect(mouseX, mouseY, app.width/2, 716, 600, 132):
        app.startButtonHover = True
    else:
        app.startButtonHover = False

def start_onMousePress(app, mouseX, mouseY):
    #'Fake' image button intersection
    if intersectionRect(mouseX, mouseY, app.width/2, 716, 600, 132):
        app.startSound.play(restart=True, loop=False)
        setActiveScreen('menu')

def start_redrawAll(app):
    #Start menu image source from Google, edited in Pixelmator
    if app.startButtonHover == True:
        drawImage('img/Start_Screen_hover.jpg', 0, 0, width=app.width, height=app.height)
    else:
        drawImage('img/Start_Screen.jpg', 0, 0, width=app.width, height=app.height)
    #Score
    drawLabel(f'High Score: {app.highScore}', app.width/2, 330, fill='white', size=35, bold=True, font='montserrat')


def menu_onScreenActivate(app):
    #Default options
    app.selectedMap = 'New York'
    app.selectedDifficulty = 'Easy'
    app.mapButtons = [
        {'label': 'New York', 'x': 250, 'y': 250},
        {'label': 'Tokyo', 'x': 500, 'y': 250},
        {'label': 'Hong Kong', 'x': 750, 'y': 250}]
    app.difficultyButtons = [
        {'label': 'Easy', 'x': 250, 'y': 550 },
        {'label': 'Medium', 'x': 500, 'y': 550 },
        {'label': 'Hard', 'x': 750, 'y': 550 }]
    app.buttonWidth = 200
    app.buttonHeight = 100

def menu_onMousePress(app, mouseX, mouseY):
    #Map button intersections
    for button in app.mapButtons:
        if intersectionRect(mouseX, mouseY, button['x'], button['y'], app.buttonWidth, app.buttonHeight):
            app.buttonSound.play(restart=True, loop=False)
            app.selectedMap = button['label']
            break
    #Difficulty button intersections
    for button in app.difficultyButtons:
        if intersectionRect(mouseX, mouseY, button['x'], button['y'], app.buttonWidth, app.buttonHeight):
            app.buttonSound.play(restart=True, loop=False)
            app.selectedDifficulty = button['label']
            break
    if intersectionRect(mouseX, mouseY, app.width/2, app.height/2 + 300, 280, 80):
        setActiveScreen('game')
        app.startSound.play(restart=True, loop=False)
        app.startTheme.pause()

def menu_onKeyPress(app, key):
    if key == 'escape':
        app.startTheme.pause()
        app.exitSound.play(loop=False)
        setActiveScreen('start')
    
def menu_redrawAll(app):
    #Button color adjustment according to difficulty
    colorMap = {'Easy': rgb(230, 250, 255), 'Medium': rgb(255, 255, 224), 'Hard': rgb(255, 230, 240)}
    highlightColor = colorMap.get(app.selectedDifficulty)

    #Background Image source Google, edited in Pixelmator
    if app.selectedMap == 'New York':
        drawImage('img/NY.jpg', 0, 0, width=app.width, height=app.height)
    elif app.selectedMap == 'Tokyo':
        drawImage('img/TK.jpg', 0, 0, width=app.width, height=app.height)
    elif app.selectedMap == 'Hong Kong':
        drawImage('img/HK.jpg', 0, 0, width=app.width, height=app.height)
    
    #Map selection UI
    drawLabel("Select Map", 100, 100, fill='aliceBlue', size=40, bold=True, font='montserrat', align='left')
    for button in app.mapButtons:
        color = highlightColor if app.selectedMap == button['label'] else 'darkGray'
        drawRoundedRect(button['x'], button['y'], app.buttonWidth, app.buttonHeight, 30, color)
        drawLabel(button['label'], button['x'], button['y'], size=30, font='montserrat', fill=rgb(80, 80, 80))

    #Difficulty selection UI
    drawLabel("Select Difficulty", 100, 400, fill='aliceBlue', size=40, font='montserrat', bold=True, align='left')
    for button in app.difficultyButtons:
        color = highlightColor if app.selectedDifficulty == button['label'] else 'darkGray'
        drawRoundedRect(button['x'], button['y'], app.buttonWidth, app.buttonHeight, 30, color)
        drawLabel(button['label'], button['x'], button['y'], size=30, font='montserrat', fill=rgb(80, 80, 80))

    #Launch game button
    drawRect(app.width/2, app.height/2 + 300, 200, 80, fill=highlightColor, align='center')
    drawCircle(app.width/2 - 100, app.height/2 + 300, 40, fill=highlightColor)
    drawCircle(app.width/2 + 100, app.height/2 + 300, 40, fill=highlightColor)
    drawLabel("Start", app.width/2, app.height/2 + 300, fill=rgb(80, 80, 80), size=40, bold=True, font='montserrat')

def drawRoundedRect(centerX, centerY, width, height, radius, fill):
    drawRect(centerX, centerY, width, height - 2*radius, fill=fill, align='center')
    drawRect(centerX, centerY, width - 2*radius, height, fill=fill, align='center')
    drawCircle(centerX - width/2 + radius, centerY - height/2 + radius, radius, fill=fill)
    drawCircle(centerX + width/2 - radius, centerY - height/2 + radius, radius, fill=fill)
    drawCircle(centerX - width/2 + radius, centerY + height/2 - radius, radius, fill=fill)
    drawCircle(centerX + width/2 - radius, centerY + height/2 - radius, radius, fill=fill)

def intersectionRect(mouseX, mouseY, centerX, centerY, width, height):
    left = centerX - width/2
    right = centerX + width/2
    top = centerY - height/2
    bottom = centerY + height/2
    return left <= mouseX <= right and top <= mouseY <= bottom


def game_onScreenActivate(app):
    app.stations = []
    app.lines = []
    app.selectedStation = None
    app.gameOver = False
    app.gameOverSoundPlayed = False
    app.timer = 0
    app.passengersTrips = 0
    #Difficulty settings
    if app.selectedDifficulty == 'Easy':
        app.passengerSpawnRate = 140 #Starts every 2.33 seconds, gradually increases in freq
        app.stationSpawnRate = 660 #Every 11 seconds
        app.stationLimit = 20
        app.spawnLimit = 30
        app.stationCapacity = 10
        app.shapes = ['circle', 'square', 'triangle']
        app.colors = ['red', 'blue', 'green', 'orange', 'purple']
    elif app.selectedDifficulty == 'Medium':
        app.passengerSpawnRate = 100 #Starts every 1.67 seconds, gradually increases in freq
        app.stationSpawnRate = 600 #Every 10 seconds
        app.stationLimit = 20
        app.spawnLimit = 20
        app.stationCapacity = 8
        app.shapes = ['circle', 'square', 'triangle', 'diamond', 'pentagon']
        app.colors = ['red', 'blue', 'green', 'orange', 'purple']
    elif app.selectedDifficulty == 'Hard':
        app.passengerSpawnRate = 80 #Starts every 1.33 seconds, gradually increases in freq
        app.stationSpawnRate = 540 #Every 9 seconds
        app.stationLimit = 30
        app.spawnLimit = 10
        app.stationCapacity = 8
        app.shapes = ['circle', 'square', 'triangle', 'diamond', 'pentagon']
        app.colors = ['red', 'blue', 'green']
    app.segment_map = {}
    app.paused = False
    app.forceNewLine = False
    
    #Initial state
    if app.selectedMap == 'New York':
        app.gameTheme = app.newYorkTheme
        app.gameTheme.play(restart=False, loop=True)
        app.stations.append(Station(650, 500, 'circle'))
        app.stations.append(Station(900, 300, 'square'))
        app.stations.append(Station(950, 700, 'triangle'))
    if app.selectedMap == 'Tokyo':
        app.gameTheme = app.tokyoTheme
        app.gameTheme.play(restart=False, loop=True)
        app.stations.append(Station(600, 600, 'circle'))
        app.stations.append(Station(800, 300, 'square'))
        app.stations.append(Station(1100, 400, 'triangle'))
    if app.selectedMap == 'Hong Kong':
        app.gameTheme = app.hongKongTheme
        app.gameTheme.play(restart=False, loop=True)
        app.stations.append(Station(600, 400, 'circle'))
        app.stations.append(Station(1200, 500, 'square'))
        app.stations.append(Station(900, 600, 'triangle'))

def game_onStep(app):
    if app.gameOver:
        if not app.gameOverSoundPlayed: #Play sound only once
            app.gameOverSound.play(restart=True, loop=False)
            app.gameOverSoundPlayed = True
        return
    app.timer += 1

    if app.passengerSpawnRate > app.spawnLimit and app.timer % 180 == 0: #Over time increase spawn freq
        app.passengerSpawnRate -= 1

    #Gemini AI - creates a map of all shared tracks
    segment_map = {}
    for line in app.lines:
        for i in range(len(line.stations) - 1):
            s1 = line.stations[i]
            s2 = line.stations[i+1]
            segment = tuple(sorted((s1, s2), key=id))
            if segment not in segment_map:
                segment_map[segment] = []
            if line not in segment_map[segment]:
                segment_map[segment].append(line)
    for segment in segment_map:
        segment_map[segment].sort(key=lambda l: l.color)
    app.segment_map = segment_map

    if app.paused:
        return
    
    for line in app.lines: #Animate trains
        for train in line.trains:
            deliveredPassengers = train.move()
            app.passengersTrips += deliveredPassengers

    if app.timer % app.passengerSpawnRate == 0 and app.stations: #Spawn passengers
        startStation = random.choice(app.stations)
        possible_destinations = [s.shape for s in app.stations if s.shape != startStation.shape]
        if possible_destinations:
            dest_shape = random.choice(possible_destinations)
            startStation.passengers.append(Passenger(dest_shape))

    if app.timer > 0 and app.timer % app.stationSpawnRate == 0: #Spawn stations
        if len(app.stations) < app.stationLimit:
            x = random.randint(100, app.width - 100)
            y = random.randint(100, app.height - 200)
            shape = random.choice(app.shapes)
            isOverlapping = any((station.x - x)**2 + (station.y - y)**2 < (station.radius * 4)**2 for station in app.stations)
            if not isOverlapping:
                app.stations.append(Station(x, y, shape))

    for station in app.stations: #Check for overcrowding
        if len(station.passengers) > app.stationCapacity:
            app.gameOver = True

def game_onMousePress(app, mouseX, mouseY):
    if app.gameOver:
        return

    clickedStation = None
    for station in app.stations:
        if (station.x - mouseX)**2 + (station.y - mouseY)**2 < station.radius**2:
            clickedStation = station
            break

    if clickedStation:
        if not app.selectedStation:
            app.selectSound.play(restart=True, loop=False)
            app.selectedStation = clickedStation #First click
        else:
            if app.selectedStation == clickedStation:
                app.unselectSound.play(restart=True, loop=False)
                app.selectedStation = None #Clicked on same station again, unselect
                return
            extendableLine, endpointStation, newStation = findExtendableLine(app.selectedStation, clickedStation)
            if extendableLine and app.forceNewLine == False: #Extend line
                app.connectSound.play(restart=True, loop=False)
                extendableLine.extendLine(newStation, endpointStation)
            else: #Create new line
                if len(app.lines) < len(app.colors):
                    app.connectSound.play(restart=True, loop=False)
                    color = app.colors[len(app.lines)]
                    new_line = Line(color)
                    new_line.linkStation(app.selectedStation)
                    new_line.linkStation(clickedStation)
                    app.lines.append(new_line)
                else:
                    app.gameOverSound.play(restart=True, loop=False)
            app.selectedStation = None #Unselect
    else:
        app.unselectSound.play(restart=True, loop=False)
        app.selectedStation = None #Clicked on empty space, unselect
        
def game_onKeyPress(app, key):
    if key == 'space' and app.gameOver: #Restart game
        app.startSound.play(restart=True, loop=False)
        game_onScreenActivate(app)
    elif key == 'space' and not app.gameOver: #Pause & unpause
        if app.paused:
            app.playSound.play(restart=True, loop=False)
        else:
            app.pauseSound.play(restart=True, loop=False)
        app.paused = not app.paused
    elif key == 'p':
        app.gameTheme.pause()
    if key == 'escape':
        if app.highScore < app.passengersTrips:
            app.highScore = app.passengersTrips #High score based on passengers delivered
        app.gameTheme.pause()
        app.exitSound.play(restart=True, loop=False)
        setActiveScreen('start')

def game_onKeyHold(app, keys):
    if 'n' in keys:
        app.forceNewLine = True

def game_onKeyRelease(app, key):
    if key == 'n':
        app.forceNewLine = False

def game_redrawAll(app):
    #Draw map, images made by myself in Pixelmator
    if app.selectedMap == 'New York':
        drawImage('img/NY_Map.jpg', 0, 0, width=app.width, height=app.height)
    elif app.selectedMap == 'Tokyo':
        drawImage('img/TK_Map.jpg', 0, 0, width=app.width, height=app.height)
    elif app.selectedMap == 'Hong Kong':
        drawImage('img/HK_Map.jpg', 0, 0, width=app.width, height=app.height)

    #Gemini AI - separating overlapping lines
    spacing = 8
    if hasattr(app, 'segment_map'):
        for segment, lines in app.segment_map.items():
            s1, s2 = segment[0], segment[1]
            n = len(lines)
            for i, line in enumerate(lines):
                offset_distance = (i - (n - 1) / 2.0) * spacing
                dx, dy = s2.x - s1.x, s2.y - s1.y
                dist = (dx**2 + dy**2)**0.5
                if dist == 0: continue   
                perp_dx, perp_dy = -dy / dist, dx / dist
                x1_off = s1.x + offset_distance * perp_dx
                y1_off = s1.y + offset_distance * perp_dy
                x2_off = s2.x + offset_distance * perp_dx
                y2_off = s2.y + offset_distance * perp_dy
                drawLine(x1_off, y1_off, x2_off, y2_off, fill=line.color, lineWidth=5)

    for line in app.lines:
        line.draw(app)

    for station in app.stations:
        station.draw()

    #Highlight stations
    if app.selectedStation:
        drawCircle(app.selectedStation.x, app.selectedStation.y, app.selectedStation.radius + 5, fill='gold', opacity=30) #Gold highlight for first selection

        for station in app.stations:
            if station != app.selectedStation:
                extendableLine, _, _ = findExtendableLine(app.selectedStation, station)

                if extendableLine:
                    #Green for available extension
                    if station.shape == 'triangle':
                        drawRegularPolygon(station.x, station.y, station.radius + 13, 3, fill=None, border='green', borderWidth=2)
                    elif station.shape == 'square':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='green', borderWidth=2, rotateAngle=45)
                    elif station.shape == 'circle':
                        drawCircle(station.x, station.y, station.radius + 4, fill=None, border='green', borderWidth=2)
                    elif station.shape == 'diamond':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='green', borderWidth=2)
                    elif station.shape == 'pentagon':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 5, fill=None, border='green', borderWidth=2)

                elif len(app.lines) < len(app.colors):
                    #Blue for available connection with new line
                    if station.shape == 'triangle':
                        drawRegularPolygon(station.x, station.y, station.radius + 13, 3, fill=None, border='blue', borderWidth=2)
                    elif station.shape == 'square':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='blue', borderWidth=2, rotateAngle=45)
                    elif station.shape == 'circle':
                        drawCircle(station.x, station.y, station.radius + 4, fill=None, border='blue', borderWidth=2)
                    elif station.shape == 'diamond':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='blue', borderWidth=2)
                    elif station.shape == 'pentagon':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 5, fill=None, border='blue', borderWidth=2)

    #UI & Info
    drawLabel("MICRO METRO", 220, 50, size=50, fill='white', bold=True, font='montserrat', opacity=50)
    drawRect(0, app.height - 100, app.width, 100, fill='dimGray', opacity = 50)
    drawLabel("USED LINES:", 38, app.height - 75, size=20, fill='white', bold=True, font='montserrat', align='left')
    for i, color in enumerate(app.colors):
        x = 50 + i * 50
        y = app.height - 40
        if i < len(app.lines):
            drawCircle(x, y, 12, fill=color, border='white', borderWidth=2)
        else:
            drawCircle(x, y, 12, fill='lightGray', border='white', borderWidth=2)

    drawLabel(f'Force new line: {app.forceNewLine} (hold n)', 300, app.height-40, fill='white', size=16, bold=True, align='left', font='montserrat')
    total_passengers = sum(len(station.passengers) for station in app.stations)
    drawLabel(f"Waiting Passengers: {total_passengers}", app.width - 60, app.height - 80, size=16, fill='white', bold=True, align='right', font='montserrat')
    drawLabel(f"Time: {app.timer // 60}s", app.width - 60, app.height - 60, size=16, fill='white', align='right', font='montserrat')
    drawLabel(f"Stations: {len(app.stations)}", app.width - 60, app.height - 40, size=16, fill='white', align='right', font='montserrat')
    drawLabel(f"Passenger demand: {1/(app.passengerSpawnRate/180):.2f}", app.width - 60, app.height - 20, size=16, fill='white', align='right', font='montserrat')
    drawLabel(f"Passengers trips: {app.passengersTrips}", app.width/2, app.height - 80, size=20, fill='paleGreen', bold=True, align='center', font='montserrat')

    if app.selectedStation: #Connection key
        drawLabel("Click another station to connect", app.width//2, 50, size=18, fill='black', bold=True, font='montserrat')
        drawLabel("Yellow: Currently selected  Green: Available connections  Blue: Create new line", app.width//2, 90, size=18, fill='black', font='montserrat')
    else:
        drawLabel("Click a station to draw lines", app.width//2, 50, size=18, fill='black', font='montserrat')

    if app.paused: #Pause symbol
        drawRect(app.width/2 - 20, app.height/2 - 100, 20, 100, fill='maroon', opacity=50)
        drawRect(app.width/2 + 20, app.height/2 - 100, 20, 100, fill='maroon', opacity=50)

    if app.gameOver: #Game over UI
        drawRect(app.width/2 - 200, app.height/2 - 75, 400, 150, fill='maroon', opacity=50)
        drawLabel("RIOTS!", app.width/2, app.height/2 - 30, size=40, fill='white', bold=True, font='montserrat')
        drawLabel("A station became overcrowded!", app.width/2, app.height/2 + 10, size=20, fill='white', font='montserrat')
        drawLabel(f"{app.passengersTrips} trips were made", app.width/2, app.height/2 + 35, size=20, fill='white', font='montserrat')
        drawLabel("Press SPACE to restart", app.width/2, app.height/2 + 90, size=20, fill='gray', bold=True, font='montserrat')

def findExtendableLine(station1, station2):
    #Priority for first selected station
    #Checks if first selected line is valid
    for line in station1.lines:
        endpoints = line.getEndpoints()
        if len(endpoints) == 2 and station1 in endpoints and station2 not in line.stations:
            return line, station1, station2
    
    #Checks if second selected line is valid
    for line in station2.lines:
        endpoints = line.getEndpoints()
        if len(endpoints) == 2 and station2 in endpoints and station1 not in line.stations:
            return line, station2, station1

    return None, None, None


def main():
    runAppWithScreens(initialScreen='start', width=1600, height=900)

main()
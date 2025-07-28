from cmu_graphics import *
import random
from collections import deque

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
                drawCircle(posX, posY, 4, fill='Gray')
            elif passenger.destinationShape == 'square':
                drawRegularPolygon(posX, posY, 6, 4, fill='Gray', rotateAngle=45)
            elif passenger.destinationShape == 'triangle':
                drawRegularPolygon(posX, posY, 6, 3, fill='Gray')
            elif passenger.destinationShape == 'diamond':
                drawRegularPolygon(posX, posY, 6, 4, fill='Gray')
            elif passenger.destinationShape == 'pentagon':
                drawRegularPolygon(posX, posY, 6, 5, fill='Gray')

class Passenger:
    #Passenger shape is determined by the destination
    def __init__(self, destinationShape):
        self.destinationShape = destinationShape
        self.transferStation = None  # Station where passenger should transfer

class Line:
    def __init__(self, color):
        self.stations = []
        self.color = color
        self.trains = []

    #Create a line
    def linkStation(self, station):
        #You cant add the same station twice for a line
        if station not in self.stations:
            self.stations.append(station) #adds station to line
            station.lines.append(self) #adds line to station
            #Condition for train existing
            if len(self.stations) == 2 and not self.trains:
                self.trains.append(Train(self, 0))

    #Extend a line
    def extendLine(self, newStation, endStation):
        if newStation in self.stations or endStation not in self.getEndpoints():
            return
        if self.stations[0] == endStation:
            self.stations.insert(0, newStation)
            for train in self.trains:
                train.currentIndex += 1
                train.targetIndex += 1
        elif self.stations[-1] == endStation:
            self.stations.append(newStation)
        newStation.lines.append(self)

    def getEndpoints(self):
        return [self.stations[0], self.stations[-1]]

    #Line drawing handled in redrawAll
    def draw(self, app):
        for train in self.trains:
            train.draw(app)

#AI
def _find_path_bfs(start_station, destination_shape):
    queue = deque([(start_station, [start_station])])
    visited = {start_station}

    if start_station.shape == destination_shape:
        return [start_station]

    while queue:
        current_station, path = queue.popleft()

        # Find adjacent stations to current_station
        neighbors = set()
        for line in current_station.lines:
            try:
                idx = line.stations.index(current_station)
                if idx > 0:
                    neighbors.add(line.stations[idx - 1])
                if idx < len(line.stations) - 1:
                    neighbors.add(line.stations[idx + 1])
            except ValueError:
                continue
        
        for neighbor in neighbors:
            if neighbor not in visited:
                new_path = path + [neighbor]
                if neighbor.shape == destination_shape:
                    return new_path  # Found the shortest path
                
                visited.add(neighbor)
                queue.append((neighbor, new_path))
    
    return None  # No path found

#AI
def findTransferRoute(startStation, destinationShape):
    path = _find_path_bfs(startStation, destinationShape)

    if not path or len(path) < 3:
        # No path exists, or the path is direct (no transfers needed).
        return None

    # Determine the lines for the first leg of the journey.
    lines_for_current_leg = set(path[0].lines) & set(path[1].lines)
    if not lines_for_current_leg:
        return None # Should not happen with a valid path

    # Iterate through the path to find the first mandatory transfer station.
    for i in range(1, len(path) - 1):
        current_station = path[i]
        next_station = path[i+1]

        lines_for_next_leg = set(current_station.lines) & set(next_station.lines)

        # If there are no shared lines between the current leg and the next,
        # a transfer is required at the current station.
        if not lines_for_current_leg.intersection(lines_for_next_leg):
            return current_station

        # Otherwise, continue on the shared lines.
        lines_for_current_leg = lines_for_current_leg.intersection(lines_for_next_leg)

    # If the loop completes, the entire journey can be made on at least one line.
    return None

class Train:
    def __init__(self, line, startIndex):
        self.line = line
        self.currentIndex = startIndex #station train is from
        self.passengers = []
        self.capacity = 6
        self.x, self.y = self.line.stations[startIndex].x, self.line.stations[startIndex].y
        self.targetIndex = (startIndex + 1) % len(self.line.stations) if len(self.line.stations) > 0 else 0
        self.speed = 1.5
        self.direction = 1
        self.waitTimer = 0 #for stopping at stations

    def move(self):
        if self.waitTimer > 0:
            self.waitTimer -= 1
            return
        if len(self.line.stations) < 2:
            return
    
        target_station = self.line.stations[self.targetIndex]
        dx = target_station.x - self.x
        dy = target_station.y - self.y
        dist = (dx**2 + dy**2)**0.5
        if dist < self.speed: #arrived, snap to target
            self.x, self.y = target_station.x, target_station.y
            self.currentIndex = self.targetIndex
            self.handlePassengers()
            #flip directions at ends
            if self.targetIndex == len(self.line.stations) - 1:
                self.direction = -1
            elif self.targetIndex == 0:
                self.direction = 1
            self.targetIndex += self.direction
            self.waitTimer = 60 #1 second
        else: #move
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    #drop and take passengers
    def handlePassengers(self):
        currentStation = self.line.stations[self.currentIndex]
        
        # Drop off passengers at their final destination
        self.passengers = [p for p in self.passengers if p.destinationShape != currentStation.shape]
        
        # Drop off passengers who need to transfer at this station
        passengers_to_transfer = []
        remaining_passengers = []
        for p in self.passengers:
            if hasattr(p, 'transferStation') and p.transferStation == currentStation:
                passengers_to_transfer.append(p)
            else:
                remaining_passengers.append(p)
        
        self.passengers = remaining_passengers
        
        # Add transfer passengers to the station
        for p in passengers_to_transfer:
            p.transferStation = None  # Reset transfer station
            currentStation.passengers.append(p)
        
        # Pick up passengers from the station
        for passenger in list(currentStation.passengers):
            if len(self.passengers) < self.capacity:
                # Check if destination is directly reachable on this line
                destinationAvailable = any(s.shape == passenger.destinationShape for s in self.line.stations)
                
                if destinationAvailable:
                    # Direct route - pick up passenger
                    self.passengers.append(passenger)
                    currentStation.passengers.remove(passenger)
                else:
                    # Check if we can find a transfer route
                    transferStation = findTransferRoute(currentStation, passenger.destinationShape)
                    if transferStation and transferStation in self.line.stations:
                        # Pick up passenger and set their transfer station
                        passenger.transferStation = transferStation
                        self.passengers.append(passenger)
                        currentStation.passengers.remove(passenger)

    def draw(self, app):
        if len(self.line.stations) < 2: return

        s2 = self.line.stations[self.targetIndex]
        s1_index = self.targetIndex - self.direction
        if not (0 <= s1_index < len(self.line.stations)):
            drawRect(self.x - 15, self.y - 7, 30, 14, fill=self.line.color, border='black', borderWidth=2) #Train
            return
    
        s1 = self.line.stations[s1_index]
        segment = tuple(sorted((s1, s2), key=id))
    
        #AI - placing trains on correct track
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
            # Calculate the perpendicular vector for the offset
            perp_dx = -dy / dist
            perp_dy = dx / dist
            draw_x += offset_distance * perp_dx
            draw_y += offset_distance * perp_dy

        # draw train and its passengers
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

def game_onScreenActivate(app):
    """Initialize or reset all game variables"""
    app.stations = []
    app.lines = []
    app.shapes = ['circle', 'square', 'triangle', 'diamond', 'pentagon']
    app.colors = ['red', 'blue', 'green', 'orange', 'purple']
    app.selectedStation = None
    app.gameOver = False
    app.timer = 0
    app.passengerSpawnRate = 120 #Starts every 2 seconds, gradually increases
    app.stationSpawnRate = 600 #Every 10 seconds
    app.segment_map = {}
    app.paused = False
    
    #Initial state
    app.stations.append(Station(600, 400, 'circle'))
    app.stations.append(Station(800, 300, 'square'))
    app.stations.append(Station(950, 500, 'triangle'))
    line = Line('red')
    line.linkStation(app.stations[0])
    line.linkStation(app.stations[1])
    app.lines.append(line)

def onAppStart(app):
    app.stepsPerSecond = 60
    app.highScore = 0

def game_onStep(app):
    if app.gameOver:
        if app.highScore < app.timer:
            app.highScore = app.timer
        return

    #AI - creates a map of all shared tracks
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
    app.timer += 1

    if app.passengerSpawnRate > 10 and app.timer % 180 == 0:
        app.passengerSpawnRate -= 1
    

    #animate trains
    for line in app.lines:
        for train in line.trains:
            train.move()

    #spawn passengers
    if app.timer % app.passengerSpawnRate == 0 and app.stations:
        startStation = random.choice(app.stations)
        possible_destinations = [s.shape for s in app.stations if s.shape != startStation.shape]
        if possible_destinations:
            dest_shape = random.choice(possible_destinations)
            startStation.passengers.append(Passenger(dest_shape))

    #spawn stations
    if app.timer > 0 and app.timer % app.stationSpawnRate == 0:
        if len(app.stations) < 20:
            x = random.randint(100, app.width - 100)
            y = random.randint(100, app.height - 200)
            shape = random.choice(app.shapes)
            isOverlapping = any((s.x - x)**2 + (s.y - y)**2 < (s.radius * 4)**2 for s in app.stations)
            if not isOverlapping:
                app.stations.append(Station(x, y, shape))

    #check for overcrowding
    for station in app.stations:
        if len(station.passengers) > 8:
            app.gameOver = True

def findExtendableLine(app, station1, station2):
    #priority for first selected station
    #checks if first selected line is valid
    for line in station1.lines:
        endpoints = line.getEndpoints()
        if len(endpoints) == 2 and station1 in endpoints and station2 not in line.stations:
            return line, station1, station2
    
    #checks if second selected line is valid
    for line in station2.lines:
        endpoints = line.getEndpoints()
        if len(endpoints) == 2 and station2 in endpoints and station1 not in line.stations:
            return line, station2, station1

    return None, None, None

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
            app.selectedStation = clickedStation #first click
        else:
            if app.selectedStation == clickedStation:
                app.selectedStation = None #clicked on same station again, unselect
                return
            extendableLine, endpointStation, newStation = findExtendableLine(app, app.selectedStation, clickedStation)
            if extendableLine: #extend line
                extendableLine.extendLine(newStation, endpointStation)
            else: #create new line
                if len(app.lines) < len(app.colors):
                    color = app.colors[len(app.lines)]
                    new_line = Line(color)
                    new_line.linkStation(app.selectedStation)
                    new_line.linkStation(clickedStation)
                    app.lines.append(new_line)
            app.selectedStation = None #clicked on empty space, unselect
    else:
        app.selectedStation = None
        
def game_onKeyPress(app, key):
    if key == 'space' and app.gameOver: #restart game
        game_onScreenActivate(app)
    elif key == 'space' and not app.gameOver: #pause & unpause
        app.paused = not app.paused
    if key == 'escape':
        setActiveScreen('start')

def game_redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='lightGoldenrodYellow') #background
    #AI - separating overlapping lines
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
        drawCircle(app.selectedStation.x, app.selectedStation.y, app.selectedStation.radius + 5, fill=None, border='gold', borderWidth=3) #gold highlight for first selection

        for station in app.stations:
            if station != app.selectedStation:
                extendableLine, _, _ = findExtendableLine(app, app.selectedStation, station)

                if extendableLine:
                    #green for available extension
                    if station.shape == 'triangle':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 3, fill=None, border='green', borderWidth=2)
                    elif station.shape == 'square':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='green', borderWidth=2, rotateAngle=45)
                    elif station.shape == 'circle':
                        drawCircle(station.x, station.y, station.radius + 3, fill=None, border='green', borderWidth=2)
                    elif station.shape == 'diamond':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='green', borderWidth=2)
                    elif station.shape == 'pentagon':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 5, fill=None, border='green', borderWidth=2)

                elif len(app.lines) < len(app.colors):
                    #blue for available connection with new line
                    if station.shape == 'triangle':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 3, fill=None, border='blue', borderWidth=2)
                    elif station.shape == 'square':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='blue', borderWidth=2, rotateAngle=45)
                    elif station.shape == 'circle':
                        drawCircle(station.x, station.y, station.radius + 3, fill=None, border='blue', borderWidth=2)
                    elif station.shape == 'diamond':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 4, fill=None, border='blue', borderWidth=2)
                    elif station.shape == 'pentagon':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 5, fill=None, border='blue', borderWidth=2)

    #UI
    drawLabel("MICRO METRO", 220, 50, size=50, fill='gray', bold=True, font='montserrat')
    drawRect(0, app.height - 100, app.width, 100, fill='darkSlateGray')
    drawLabel("USED LINES:", 38, app.height - 75, size=20, fill='white', bold=True, font='montserrat', align='left')
    for i, color in enumerate(app.colors):
        x = 50 + i * 50
        y = app.height - 40
        if i < len(app.lines):
            drawCircle(x, y, 12, fill=color, border='white', borderWidth=2)
        else:
            drawCircle(x, y, 12, fill='lightGray', border='white', borderWidth=2)
    
    #Info display
    total_passengers = sum(len(station.passengers) for station in app.stations)
    drawLabel(f"Waiting Passengers: {total_passengers}", app.width - 60, app.height - 80, size=16, fill='white', bold=True, align='right', font='montserrat')
    drawLabel(f"Time: {app.timer // 60}s", app.width - 60, app.height - 60, size=16, fill='white', align='right', font='montserrat')
    drawLabel(f"Stations: {len(app.stations)}", app.width - 60, app.height - 40, size=16, fill='white', align='right', font='montserrat')
    drawLabel(f"Lines: {len(app.lines)}", app.width - 60, app.height - 20, size=16, fill='white', align='right', font='montserrat')
    drawLabel(f"Passenger Spawn Rate: {(app.passengerSpawnRate / 60):.3f} per second", app.width - 500, app.height - 80, size=16, fill='white', bold=True, align='right', font='montserrat')

    if app.selectedStation:
        drawLabel("Click another station to connect", app.width//2, app.height - 200, size=18, fill='black', bold=True, font='montserrat')
        drawLabel("Yellow: Currently selected  Green: Available connections  Blue: Create new line", app.width//2, app.height - 150, size=18, fill='black', font='montserrat')
    else:
        drawLabel("Click a station to draw lines", app.width//2, app.height - 200, size=18, fill='black', font='montserrat')

    if app.paused:
        drawRect(app.width/2 - 20, app.height/2 - 100, 20, 100, fill='maroon', opacity=50)
        drawRect(app.width/2 + 20, app.height/2 - 100, 20, 100, fill='maroon', opacity=50)

    if app.gameOver:
        drawRect(app.width/2 - 200, app.height/2 - 75, 400, 150, fill='maroon', opacity=50)
        drawLabel("RIOTS!", app.width/2, app.height/2 - 30, size=40, fill='white', bold=True, font='montserrat')
        drawLabel("A station became overcrowded!", app.width/2, app.height/2 + 10, size=20, fill='white', font='montserrat')
        drawLabel(f"You survived {app.timer // 60} seconds", app.width/2, app.height/2 + 35, size=20, fill='white', font='montserrat')
        drawLabel("Press SPACE to restart", app.width/2, app.height/2 + 90, size=20, fill='gray', bold=True, font='montserrat')

def start_onScreenActivate(app):
    pass

def start_onMousePress(app, mouseX, mouseY):
    if intersectionRect(mouseX, mouseY, app.width/2, app.height/2 + 200, 280, 80):
        setActiveScreen('menu')

def start_redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='aliceBlue') #background
    #Logo
    drawLabel('MICRO', app.width/2 - 200, app.height/2 - 140, fill=gradient('darkRed','crimson', start='bottom'), size=100, bold=True, font='montserrat')
    drawLabel('METRO', app.width/2 + 200, app.height/2 - 140, fill=gradient('darkRed','crimson',start='bottom'), size=100, bold=True, font='montserrat')
    #play button
    drawRect(app.width/2, app.height/2 + 200, 200, 80, fill='cornflowerBlue', align='center')
    drawCircle(app.width/2 - 100, app.height/2 + 200, 40, fill='cornflowerBlue')
    drawCircle(app.width/2 + 100, app.height/2 + 200, 40, fill='cornflowerBlue')
    drawLabel("Play", app.width/2, app.height/2 + 200, fill='aliceBlue', size=40, bold=True, font='montserrat')
    #Score
    drawLabel(f'High Score: {app.highScore}', app.width/2, app.height/2 + 60, size=20, font='montserrat')

def menu_onScreenActivate(app):
    app.gameSelected = False
    app.selectedMap = None
    app.selectedDifficulty = None
    app.mapButtons = [
        {'label': 'New York', 'x': 250, 'y': 250 },
        {'label': 'Tokyo', 'x': 650, 'y': 250 },
        {'label': 'Hong Kong', 'x': 1050, 'y': 250 }
    ]
    app.difficultyButtons = [
        {'label': 'Easy', 'x': 250, 'y': 550 },
        {'label': 'Medium', 'x': 650, 'y': 550 },
        {'label': 'Hard', 'x': 1050, 'y': 550 }
    ]
    app.buttonWidth = 300
    app.buttonHeight = 180

def menu_onMousePress(app, mouseX, mouseY):
    for button in app.mapButtons:
        if intersectionRect(mouseX, mouseY, button['x'], button['y'], app.buttonWidth, app.buttonHeight):
            app.selectedMap = button['label']
            break
    for button in app.difficultyButtons:
        if intersectionRect(mouseX, mouseY, button['x'], button['y'], app.buttonWidth, app.buttonHeight):
            app.selectedDifficulty = button['label']
            break
    if app.selectedMap != None and app.selectedDifficulty != None:
        app.gameSelected = True
    if intersectionRect(mouseX, mouseY, app.width/2, app.height/2 + 300, 280, 80) and app.gameSelected:
        setActiveScreen('game')

def menu_onKeyPress(app, key):
    if key == 'escape':
        setActiveScreen('start')
    
def menu_redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='aliceBlue') #background
    #Map selection UI
    drawLabel("Select Map", 100, 100, fill='cornflowerBlue', size=40, font='montserrat', align='left')
    for button in app.mapButtons:
        color = 'cornflowerBlue' if app.selectedMap == button['label'] else 'lightGray'
        drawRoundedRect(button['x'], button['y'], app.buttonWidth, app.buttonHeight, 40, color)
        drawLabel(button['label'], button['x'], button['y'], size=30, font='montserrat')
    #Difficulty selection UI
    drawLabel("Select Difficulty", 100, 400, fill='cornflowerBlue', size=40, font='montserrat', align='left')
    for button in app.difficultyButtons:
        color = 'cornflowerBlue' if app.selectedDifficulty == button['label'] else 'lightGray'
        drawRoundedRect(button['x'], button['y'], app.buttonWidth, app.buttonHeight, 40, color)
        drawLabel(button['label'], button['x'], button['y'], size=30, font='montserrat')
    #Launch game button
    if app.gameSelected:
        buttonColor = 'cornflowerBlue'
    else:
        buttonColor = 'lightGray'
    drawRect(app.width/2, app.height/2 + 300, 200, 80, fill=buttonColor, align='center')
    drawCircle(app.width/2 - 100, app.height/2 + 300, 40, fill=buttonColor)
    drawCircle(app.width/2 + 100, app.height/2 + 300, 40, fill=buttonColor)
    drawLabel("Play", app.width/2, app.height/2 + 300, fill='aliceBlue', size=40, bold=True, font='montserrat')

def drawRoundedRect(centerX, centerY, width, height, radius, fill):
    radius = min(abs(radius), width / 2, height / 2)
    drawRect(centerX, centerY, width, height - 2 * radius, fill=fill, align='center')
    drawRect(centerX, centerY, width - 2 * radius, height, fill=fill, align='center')
    drawCircle(centerX - width / 2 + radius, centerY - height / 2 + radius, radius, fill=fill)
    drawCircle(centerX + width / 2 - radius, centerY - height / 2 + radius, radius, fill=fill)
    drawCircle(centerX - width / 2 + radius, centerY + height / 2 - radius, radius, fill=fill)
    drawCircle(centerX + width / 2 - radius, centerY + height / 2 - radius, radius, fill=fill)

def intersectionRect(mouseX, mouseY, centerX, centerY, width, height):
    left = centerX - width / 2
    right = centerX + width / 2
    top = centerY - height / 2
    bottom = centerY + height / 2
    return left <= mouseX <= right and top <= mouseY <= bottom

def main():
    runAppWithScreens(initialScreen='start', width=1600, height=900)

main()
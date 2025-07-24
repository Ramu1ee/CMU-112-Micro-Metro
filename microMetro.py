#Micro Metro is inspired by the game 'Mini Metro'

from cmu_graphics import *
import random

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
            drawRect(self.x, self.y, 2 * self.radius, 2 * self.radius, fill='white', border='black', borderWidth=3, align='center')
        elif self.shape == 'triangle':
            drawRegularPolygon(self.x, self.y, self.radius + 5, 3, fill='white', border='black', borderWidth=3)

        #Draw passengers waiting at station
        for i, passenger in enumerate(self.passengers):
            posX = self.x - 20 + (i % 5) * 10
            posY = self.y + 30 + (i // 5) * 10
            if passenger.destinationShape == 'circle':
                drawCircle(posX, posY, 4, fill='Gray')
            elif passenger.destinationShape == 'square':
                drawRect(posX, posY, 8, 8, fill='Gray', align='center')
            elif passenger.destinationShape == 'triangle':
                drawRegularPolygon(posX, posY, 6, 3, fill='Gray')

class Passenger:
    #Passenger shape is determined by the destination
    def __init__(self, destinationShape):
        self.destinationShape = destinationShape

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
        self.passengers = [p for p in self.passengers if p.destinationShape != currentStation.shape] #drop off
        for passenger in list(currentStation.passengers): #pick up
            if len(self.passengers) < self.capacity:
                destinationAvailable = any(s.shape == passenger.destinationShape for s in self.line.stations)
                if destinationAvailable:
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
        
        #Gemini AI - makes lines not overlap
        offset_distance = 0
        if hasattr(app, 'segment_map') and segment in app.segment_map:
            shared_lines = app.segment_map[segment]
            n = len(shared_lines)
            if self.line in shared_lines:
                line_index = shared_lines.index(self.line)
                spacing = 8
                offset_distance = (line_index - (n - 1) / 2.0) * spacing

        dx = s2.x - s1.x
        dy = s2.y - s1.y
        dist = (dx**2 + dy**2)**0.5
        
        draw_x, draw_y = self.x, self.y
        if dist > 0:
            perp_dx = -dy / dist
            perp_dy = dx / dist
            draw_x += offset_distance * perp_dx
            draw_y += offset_distance * perp_dy

        #train and passengers on train
        drawRect(draw_x - 15, draw_y - 7, 30, 14, fill=self.line.color, border='black', borderWidth=2)
        for i, p in enumerate(self.passengers):
            px = draw_x - 10 + (i % 3) * 10
            py = draw_y + (i // 3 - 0.5) * 8
            if p.destinationShape == 'circle':
                drawCircle(px, py, 3, fill='white')
            elif p.destinationShape == 'square':
                drawRect(px, py, 5, 5, fill='white', align='center')
            elif p.destinationShape == 'triangle':
                drawRegularPolygon(px, py, 4, 3, fill='white')

def onAppStart(app):
    app.stepsPerSecond = 60
    app.stations = []
    app.lines = []
    app.shapes = ['circle', 'square', 'triangle']
    app.colors = ['red', 'blue', 'green', 'orange', 'purple']
    app.selectedStation = None
    app.gameOver = False
    app.timer = 0
    app.passengerSpawnRate = 80 #Every 8/6 seconds
    app.stationSpawnRate = 720 #Every 12 seconds
    app.score = 0
    app.segment_map = {}
    
    #Initial state
    app.stations.append(Station(200, 200, 'circle'))
    app.stations.append(Station(400, 300, 'square'))
    app.stations.append(Station(300, 500, 'triangle'))
    line = Line('red')
    line.linkStation(app.stations[0])
    line.linkStation(app.stations[1])
    app.lines.append(line)

def onStep(app):
    if app.gameOver:
        return
    app.timer += 1
    
    #Gemini AI
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

def onMousePress(app, mouseX, mouseY):
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

def onKeyPress(app, key):
    pass

def redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='lightGoldenrodYellow') #background

    #AI - Gemini helped with separating lines when multiple lines between 2 stations.
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
                        drawRect(station.x, station.y, 46, 46, fill=None, border='green', borderWidth=2, align='center')
                    elif station.shape == 'circle':
                        drawCircle(station.x, station.y, station.radius + 3, fill=None, border='green', borderWidth=2)

                elif len(app.lines) < len(app.colors):
                    #blue for available connection with new line
                    if station.shape == 'triangle':
                        drawRegularPolygon(station.x, station.y, station.radius + 12, 3, fill=None, border='blue', borderWidth=2)
                    elif station.shape == 'square':
                        drawRect(station.x, station.y, 46, 46, fill=None, border='blue', borderWidth=2, align='center')
                    elif station.shape == 'circle':
                        drawCircle(station.x, station.y, station.radius + 3, fill=None, border='blue', borderWidth=2)

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

    if app.selectedStation:
        drawLabel("Click another station to connect", app.width//2, app.height - 200, size=18, fill='black', bold=True, font='montserrat')
        drawLabel("Yellow: Currently selected  Green: Available connections  Blue: Create new line", app.width//2, app.height - 150, size=18, fill='black', font='montserrat')
    else:
        drawLabel("Click a station to draw lines", app.width//2, app.height - 200, size=18, fill='black', font='montserrat')

    if app.gameOver:
        drawRect(app.width/2 - 200, app.height/2 - 75, 400, 150, fill='maroon', opacity=50)
        drawLabel("RIOTS!", app.width/2, app.height/2 - 30, size=40, fill='white', bold=True, font='montserrat')
        drawLabel("A station became overcrowded!", app.width/2, app.height/2 + 10, size=20, fill='white', font='montserrat')
        drawLabel(f"You survived {app.timer // 60} seconds", app.width/2, app.height/2 + 35, size=20, fill='white', font='montserrat')

def main():
    runApp(width=1600, height=900)

main()
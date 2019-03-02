import bottle
import os
from Queue import PriorityQueue

# Constants
xpos,ypos = 0,1
cell_value = {
        'wall':-1,
        'empty':0,
        'food':10,
    }

movement_cost = {
        'default':1,
        'slow':5
    }

behaviour_trigger = {
        'starve':25
    }

directions = {
        'ortho':[(-1,0),(0,-1),(1,0),(0,1)],
        'diag': [(-1,1),(-1,-1),(1,-1),(1,1)]
     }

# Classes
class cPlayfield():
    _fields = {}
    def __init__(self, w, h):
        self.width = w
        self.height = h

        self._fields['obstacles'] = [[cell_value['empty'] for y in range(h)] for x in range(w)]
        self._fields['movecosts'] = [[movement_cost['default'] for y in range(h)] for x in range(w)]

    def __getitem__(self, id):
        return self._fields[id]

    def inBounds(self, pos):
        return ((pos[xpos] >= 0 and pos[xpos] < self.width) \
                and (pos[ypos] >= 0 and pos[ypos] < self.height))

class cSnake():
    _map = {}
    def __init__(self, s):
        self._map['id'] = s['id']
        self._map['health'] = s['health']
        self._map['length'] = s['length']
        self._map['name'] = s['name']
        self._map['body'] = [(p['x'],p['y']) for p in s['body']]
        
        self._map['head'] = self._map['body'][0]
        self._map['tail'] = self._map['body'][-1]
        self._map['starving'] = False
        if self._map['health'] <= behaviour_trigger['starve']:
            self._map['starving'] = True

    def __getitem__(self, key):
        return self._map[key]

# Helper functions
def processSnakes(snakes):
    slist = []
    for s in snakes:
        if s['health'] > 0:
            slist.append(cSnake(s))
    return slist

def processFood(food):
    flist = []
    for f in food:
        flist.append((f['x'],f['y']))
    return flist

def processPrey(snakes, ourSnake):
    plist = []
    for p in snakes:
        if p['length'] < ourSnake['length']:
            plist.append((p['head'][xpos],p['head'][ypos]))
    return plist

def findNearestFood(food, ourSnake):
    target = food[0]
    dist = (food[0][xpos] - ourSnake['head'][xpos]) + (food[0][ypos] - ourSnake['head'][ypos])
    for f in food:
        newDist = (f[xpos] - ourSnake['head'][xpos]) + (f[ypos] - ourSnake['head'][ypos])
        if newDist < dist:
            dist = newDist
            target = f
    return target

def findNeighbors(pos, directions):
    c = []
    for d in directions:
        c.append((d[xpos] + pos[xpos],d[ypos] + pos[ypos]))
    return c

def placeHalo(playfield, key, pos, targets, value):
    targets = findNeighbors(pos, targets)
    for t in targets:
        if playfield.inBounds(t):
            playfield[key][t[xpos]][t[ypos]] = value

def findShortestPath(playfield, start, target):
    distanceScore = [[(abs(x - start[xpos])+abs(y - start[ypos])) for y in range(playfield.height)] for x in range(playfield.width)]

    prevCells = {}
    totalCost = {}

    prevCells[target] = None
    totalCost[target] = 0

    openCells = PriorityQueue()
    openCells.put(target, 0)

    while (not openCells.empty()):
        currCell = openCells.get()
        if (currCell == start):
            break
        neighbors = findNeighbors(currCell, directions['ortho'])
        for n in neighbors:
            if (not playfield.inBounds(n)):
                continue
            if (playfield['obstacles'][n[xpos]][n[ypos]] == cell_value['wall']):
                continue
            newCost = totalCost[currCell] + playfield['movecosts'][n[xpos]][n[ypos]]
            if ((n not in totalCost) or (newCost < totalCost[n])):
                totalCost[n] = newCost
                openCells.put(n, newCost + distanceScore[n[xpos]][n[ypos]])
                prevCells[n] = currCell
    return prevCells

# Web endpoints
@bottle.route('/')
def static():
    return "the server is running"

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')

@bottle.post('/start')
def start():
    data = bottle.request.json

    return {
        'color': '#808FFF',
        'headType': 'smile',
        'tailType': 'regular'
    }

@bottle.post('/end')
def end():
    return "ack"

@bottle.post('/move')
def move():
    data = bottle.request.json
    
    movementOptions = {(0,-1):'up', (0,1):'down', (-1,0):'left', (1,0):'right'}
    nextMove = 'down'

    playfield = cPlayfield(data['board']['width'],data['board']['height'])
    snakeList = processSnakes(data['board']['snakes'])
    ourSnake = cSnake(data['you'])

    foodList = processFood(data['board']['food'])
    preyList = processPrey(snakeList, ourSnake)

    for snake in snakeList:
        if (snake['id'] != ourSnake['id']) and (snake['length'] >= ourSnake['length']):
            placeHalo(playfield, 'obstacles', snake['head'], directions['ortho'], cell_value['wall'])
            placeHalo(playfield, 'movecosts', snake['head'], directions['diag'], movement_cost['slow'])
        elif not ourSnake['starving']:
            # hunt smaller snakes
            trash = 1+1

        neighbors = findNeighbors(snake['head'],directions['ortho'])
        potentialGrowth = False
        for n in neighbors:
            if (n in foodList) and (playfield.inBounds(n)):
                potentialGrowth = True
                
        for part in snake['body']:
            if (part == snake['tail']) and (not potentialGrowth):
                continue
            if playfield.inBounds(part):
                playfield['obstacles'][part[xpos]][part[ypos]] = cell_value['wall']

    target = findNearestFood(foodList, ourSnake)
    if target:
        path = findShortestPath(playfield, ourSnake['head'], target)
        nextCell = path[ourSnake['head']]
        nextMove = movementOptions[(nextCell[xpos] - ourSnake['head'][xpos],nextCell[ypos] - ourSnake['head'][ypos])]

    return {
        'move': nextMove,
    }

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug = True)

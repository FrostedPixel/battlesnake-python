import bottle
import os
from random import randint
from Queue import PriorityQueue

# Constants
cellValue = {
        'obst':-1,
        'empty':0,
        'food':10,
    }

directions = {
        'ortho':[(-1,0),(0,-1),(1,0),(0,1)],
        'diag': [(-1,1),(-1,-1),(1,-1),(1,1)]
     }

# Classes
class cBoard():
    _fields = {}
    def __init__(self, w, h):
        self.width = w
        self.height = h

        self._fields['obstacles']   = [[cellValue['empty'] for y in range(h)] for x in range(w)]
        self._fields['foods']       = []
        self._fields['prey']        = []
        self._fields['movecosts']   = [[1 for y in range(h)] for x in range(w)]

    def __getitem__(self, id):
        return self._fields[id]

    def inBounds(self, pos):
        return ((pos[0] >= 0 and pos[0] < self.width) \
                and (pos[1] >= 0 and pos[1] < self.height))

    def openNeighbours(self, pos):
        neighbours = []
        for dr in directions['ortho']:
            xpos,ypos = pos[0] + dr[0],pos[1] + dr[1]
            if self.inBounds((xpos,ypos)):
                if self._fields['obstacles'][xpos][ypos] != cellValue['obst']:
                    neighbours.append((xpos,ypos))
        return neighbours

    def findNearestTarget(self, pos, key):
        if len(self._fields[key]) == 0:
            return None
        nearestTarget = self._fields[key][0]
        targetDistance = self.width * self.height
        for fd in self._fields[key]:
            dist = self.findDistance(pos,fd)
            if(dist < targetDistance):
                targetDistance = dist
                nearestTarget = fd
        return nearestTarget

    def findNearestFood(self, pos):
        return self.findNearestTarget(pos, 'foods')

    def findNearestPrey(self, pos):
        return self.findNearestTarget(pos, 'prey')

    def findDistance(self, apos, bpos):
        return (abs(apos[0] - bpos[0]) + abs(apos[1] - bpos[1]))

    def addObstacles(self, obst):
        for ob in obst:
            if self.inBounds(ob):
                self._fields['obstacles'][ob[0]][ob[1]] = cellValue['obst']

    def addFoods(self, foods):
        self._fields['foods'] = foods

    def addPrey(self, prey):
        self._fields['prey'] = prey

class cSnake():
    _map = {}
    def __init__(self, s):
        self._map['id']     = s['id']
        self._map['health'] = s['health']
        self._map['length'] = len(s['body'])
        self._map['body']   = [(p['x'],p['y']) for p in s['body']]

        self._map['head']   = self._map['body'][0]
        self._map['tail']   = self._map['body'][-1]

    def __getitem__(self, key):
        return self._map[key]

def findShortestPath(playfield, start, target):
    distanceScore = [[(abs(x - start[0])+abs(y - start[1])) for y in range(playfield.height)] for x in range(playfield.width)]

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
        neighbors = playfield.openNeighbours(currCell)
        for nb in neighbors:
            newCost = totalCost[currCell] + playfield['movecosts'][nb[0]][nb[1]]
            if ((nb not in totalCost) or (newCost < totalCost[nb])):
                totalCost[nb] = newCost
                openCells.put(nb, newCost + distanceScore[nb[0]][nb[1]])
                prevCells[nb] = currCell
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

@bottle.post('/ping')
def ping():
    return "pong"

@bottle.post('/move')
def move():
    data = bottle.request.json

    movementOptions = {(0,-1):'up', (0,1):'down', (-1,0):'left', (1,0):'right'}
    nextMove = 'down'

    gameBoard   = cBoard(data['board']['width'],data['board']['height'])
    ourSnake    = cSnake(data['you'])

    preyList = []
    for sk in data['board']['snakes']:
        if len(sk['body']) > ourSnake['length']:
            preyList.append((sk['body'][0]['x'],sk['body'][0]['y']))
        for seg in sk['body']:
            gameBoard.addObstacles([(seg['x'],seg['y'])])

    gameBoard.addPrey(preyList)

    foodList    = [(fd['x'],fd['y']) for fd in data['board']['food']]
    gameBoard.addFoods(foodList)

    gameBoard['obstacles'][ourSnake['head'][0]][ourSnake['head'][1]] = cellValue['empty']

    if len(preyList) > 0:
        target = gameBoard.findNearestPrey(ourSnake['head'])
    else:
        target = gameBoard.findNearestFood(ourSnake['head'])

    if not target:
        target = ourSnake['tail']

    path = findShortestPath(gameBoard, ourSnake['head'], target)

    if ourSnake['head'] in path:
        nextCell = path[ourSnake['head']]
    else:
        neighbours = gameBoard.openNeighbours(ourSnake['head'])
        nextCell = neighbours[randint(0,len(neighbours) - 1)]

    return {
        'move': movementOptions[(nextCell[0] - ourSnake['head'][0], nextCell[1] - ourSnake['head'][1])],
    }

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host = os.getenv('IP', '0.0.0.0'),
        port = os.getenv('PORT', '8080'),
        debug = True)

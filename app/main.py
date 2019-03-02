import bottle
import os
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

    def findNearestFood(self, pos):
        nearestFood = self._fields['foods'][0]
        foodDistance = self.width * self.height
        for fd in self._fields['foods']:
            dist = self.findDistance(pos,fd)
            if(dist < foodDistance):
                foodDistance = dist
                nearestFood = fd
        return nearestFood

    def findDistance(self, apos, bpos):
        return (abs(apos[0] - bpos[0]) + abs(apos[1] - bpos[1]))

    def addObstacles(self, obst):
        for ob in obst:
            if self.inBounds(ob):
                self._fields['obstacles'][ob[0]][ob[1]] = cellValue['obst']

    def addFoods(self, foods):
        self._fields['foods'] = foods

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
    for sk in data['board']['snakes']:
        gameBoard.addObstacles((sk['body']['x'],sk['body']['y']))

    foodList    = [(fd['x'],fd['y']) for fd in data['board']['food']]
    gameBoard.addFoods(foodList)

    gameBoard['obstacles'][ourSnake['head'][0]][ourSnake['head'][1]] = cellValue['empty']

    target = gameBoard.findNearestFood(ourSnake['head'])
    path = findShortestPath(gameBoard, ourSnake['head'], target)

    nextCell = path[ourSnake['head']]
    print "t:",target,"h:",ourSnake['head'],"p:",path[ourSnake['head']],"m:",movementOptions[(nextCell[0] - ourSnake['head'][0], nextCell[1] - ourSnake['head'][1])]

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

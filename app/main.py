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
        self._fields['food']        = [[cellValue['empty'] for y in range(h)] for x in range(w)]
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

    def findDistance(self, apos, bpos):
        return (abs(apos[0] - bpos[0]) + abs(apos[1] - bpos[1]))

    def addObstacles(self, obst):
        for ob in obst:
            if self.inBounds(ob):
                self._fields['obstacles'][ob[0]][ob[1]] = cellValue['obst']

    def addFoods(self, food):
        for fd in food:
            if self.inBounds(fd):
                self._fields['food'][fd[0]][fd[1]] = cellValue['food']

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

def findNeighbors(pos, directions):
    c = []
    for d in directions:
        c.append((d[0] + pos['x'],d[1] + pos['y']))
    return c

def findShortestPath(playfield, start, target):
    distanceScore = [[(abs(x - start['x'])+abs(y - start['y'])) for y in range(playfield.height)] for x in range(playfield.width)]

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
            if (playfield['obstacles'][n[0]][n[1]] == cellValue['obst']):
                continue
            newCost = totalCost[currCell] + playfield['movecosts'][n[0]][n[1]]
            if ((n not in totalCost) or (newCost < totalCost[n])):
                totalCost[n] = newCost
                openCells.put(n, newCost + distanceScore[n[0]][n[1]])
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
    
@bottle.post('/ping')
def ping():
    return "pong"

@bottle.post('/move')
def move():
    data = bottle.request.json

    #movementOptions = {(0,-1):'up', (0,1):'down', (-1,0):'left', (1,0):'right'}
    nextMove = 'down'

    gameBoard = cBoard(data['board']['width'],data['board']['height'])
    ourSnake = cSnake(data['you'])

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

import bottle
import os
import random
from Queue import PriorityQueue
from operator import itemgetter

symbols = {
    'wall':-1,
    'empty':0,
    'slow':5,
    'food':10,
    'orth':[(0,1),(1,0),(0,-1),(-1,0)],
    'diag':[(1,1),(-1,-1),(1,-1),(-1,1)],
    }

class cBoard():
    field = []
    width = 0
    height = 0
    def __init__(self, b):
        self.field = b
        self.width = len(b)
        self.height = len(b[0])

    def __getitem__(self, id):
        return self.field[id]

    def toString():
        output = ""
        for r in board:
            for c in r:
                 output += str(c).zfill(2)
            output += '\n'
        return output

class point(tuple):
    __slots__ = []
    def __new__(cls, x, y):
        return tuple.__new__(cls, (x, y))
    x = property(itemgetter(0))
    y = property(itemgetter(1))
    def __str__(self):
        if self is not None:
            return str(self.x) + "," + str(self.y)
        else:
            return "noPt"
    def __eq__(self,other):
        return self.x == other.x and self.y == other.y

    def __add__(self,other):
        return point(self.x + other.x, self.y + other.y)

    def __sub__(self,other):
        return point(self.x - other.x, self.y - other.y)

def clampValue(val, min, max):
    if val < min:
        return min
    if val > max:
        return max
    return val

def printDic(dic):
    for key,value in dic.items():
        print "key " + str(key) + " : val " + str(value)

def removeDeadChallengers(challengers):
    livingSnakes = []
    for snake in challengers:
        if snake['health'] > 0:
            livingSnakes.append(snake)
    return livingSnakes

def placeHalo(board, snake, targets, val):
    for target in targets:
        candidate = point(clampValue(snake.x + target[0], 0, board.width - 1), \
            clampValue(snake.y + target[1], 0, board.height - 1))
        if (snake == candidate):
            continue
        board[candidate.x][candidate.y] = val

def shortestPath(board, startPoint, endPoint):
    distScore = [[abs(i - startPoint.x)+abs(j - startPoint.y) for i in range(board.width)] for j in range(board.height)]

    cameFrom = {}
    costSoFar = {}
    cameFrom[endPoint] = None

    costSoFar[endPoint] = 0
    openList = PriorityQueue()
    openList.put(endPoint, 0)

    while not openList.empty():
        currentPoint = openList.get()
        for dir in symbols['orth']:
            x = clampValue(currentPoint.x+dir[0], 0, board.width  - 1)
            y = clampValue(currentPoint.y+dir[1], 0, board.height - 1)
            nextPoint = point(x, y)
            newCost = costSoFar[currentPoint] + board[x][y]
            if board[x][y] != symbols['wall'] and (nextPoint not in costSoFar or newCost < costSoFar[nextPoint]):
                costSoFar[nextPoint] = newCost
                openList.put(nextPoint, newCost + distScore[x][y])
                cameFrom[nextPoint] = currentPoint
    return cameFrom

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
        'color': '#00FF00',
        'taunt': 'Where\'s the food?',
        'head_type': 'smile',
        'tail_type': 'regular'
    }

@bottle.post('/end')
def end():
    return "ack"

@bottle.post('/move')
def move():
    data = bottle.request.json
    directions = {point(0,-1):'up', point(0,1):'down', point(-1,0):'left', point(1,0):'right'}

    you = data['you']
    startX = int(you['body']['data'][0]['x'])
    startY = int(you['body']['data'][0]['y'])
    startPoint = point(startX, startY)

    # generate board, and fill with movement cost of '1'
    field = [[1 for x in range(int(data['width']))] for y in range(int(data['height']))]
    board = cBoard(field)

    # get challengers, and remove dead opponents
    challengers = data['snakes']['data']
    challengers = removeDeadChallengers(challengers)

    # mark challengers as 'walls' on board
    for snake in challengers:
        snakePos = point(snake['body']['data'][0]['x'], \
                snake['body']['data'][0]['y'])
        if (snake['id'] != you['id']) and (snake['length'] >= you['length']):
            placeHalo(board,snakePos,symbols['diag'],symbols['slow'])
            placeHalo(board,snakePos,symbols['orth'],symbols['wall'])
    for snake in challengers:
        for segment in snake['body']['data']:
            board[segment['x']][segment['y']] = symbols['wall']

    # find nearest food
    endPoint = point(data['food']['data'][0]['x'],data['food']['data'][0]['y'])
    distanceToFood = (abs(endPoint.x - startPoint.x) + abs(endPoint.y - startPoint.y))
    for food in data['food']['data']:
        currentDistance = (abs(endPoint.x - food['x']) + \
                abs(endPoint.y - food['y']))
        if (currentDistance < distanceToFood):
            distanceToFood = currentDistance
            endPoint = point(food['x'],food['y'])

    # find shortest path to food
    path = shortestPath(board, startPoint, endPoint)
    # direction = random.choice(directions)

    print "Sanity check startPoint = " + str(startPoint) + " x,y = " + str(startX) + "," + str(startY)
    print "endPoint " + str(endPoint)

    pathAsList = []
    curPt = startPoint
    iters = 0
    while curPt != endPoint and iters < 50:
        if curPt not in path:
            break;
        curPt = path[curPt]
        pathAsList.append(curPt)
        iters += 1

    print pathAsList

    firstSquare = path[startPoint]

    squareToMoveTo = firstSquare  - startPoint
    if squareToMoveTo in directions:
        dirToMove = directions[squareToMoveTo]
    else:
        dirToMove = 'right'

    return {
        'move': dirToMove,
        'taunt': 'battlesnake-python!'
    }

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    field = [[1 for i in range(10)] for j in range(10)]
    test = cBoard(field)
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug = True)

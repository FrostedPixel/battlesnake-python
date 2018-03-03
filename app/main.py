import bottle
import os
import random
import numpy

WALL  = -1
EMPTY = 0
FOOD  = 10

def calculateZones(width, height, snake, challengers):
    zones = numpy.zeroes((width,height))
    return zones

def calculateWeights(width, height, challengers, food):
    weights = numpy.zeroes((width,height))
    return weights

def removeDeadChallengers(challengers):
    livingSnakes = []
    for x in range(len(challengers)):
        if challengers[x]['health'] > 0:
            livingSnakes.append(challengers[x])
    return livingSnakes

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
        'taunt': 'Where is the food?',
        'head_type': 'smile',
        'tail_type': 'regular'
    }

@bottle.post('/end')
def end():
    return "ack"

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

def printBoard(board):
    for row in board:
        for cell in row:
            print str(cell).zfill(2),
        print

def clamp(val, min, max):
    if val < min:
        return min
    if val > max:
        return max
    return val

def printDic(dic):
    for key,value in dic.items():
        print "key " + str(key) + " : val " + str(value)

def shortestPath(board, startPt, goal):
    FSCORE = [[abs(i - startPt.x)+abs(j - startPt.y) for i in range(10)] for j in range(10)]
    for i in range(10):
        for j in range(10):
            if board[i][j] == WALL:
                FSCORE[i][j] = 10000
    # could replace with otheer weights if want to avoid snake heads
    # read this as costs 1 turn to make a move (could switch with 1 in our or small enenmy zone and 3 in big enenmy zone or w/e)
    GWEGIHT = [[1 for i in range(10)] for j in range(10)]
    came_from = {}
    cost_so_far = {}
    came_from[goal] = None

    cost_so_far[goal] = 0
    openList = PriorityQueue()
    openList.put(goal, 0)

    iters = 0

    while not openList.empty():
        iters += 1

        curPt = openList.get()
        for dir in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            x = clamp(curPt.x+dir[0], 0, 9)
            y = clamp(curPt.y+dir[1], 0, 9)
            nextPt = point(x, y)
            newCost = cost_so_far[curPt] + GWEGIHT[x][y]
            if board[x][y] != WALL and (nextPt not in cost_so_far or newCost < cost_so_far[nextPt]):
                cost_so_far[nextPt] = newCost
                openList.put(nextPt, newCost + FSCORE[x][y])
                came_from[nextPt] = curPt
    return came_from

@bottle.post('/move')
def move():
    data = bottle.request.json
    directions = ['up', 'down', 'left', 'right']

    challengers = data.get('snakes').get('data')
    challengers = removeDeadChallengers(challangers)

    board = numpy.zeroes((data.get('width'),data.get('height')))
    zones = calculateZones(data.get('width'), data.get('height'), data.get('you'), challengers)
    weights = calculateWeights(data.get('width'), data.get('height'), challengers, data.get('food'))
    board = zones * weight

    # TODO: Do things with data

    direction = random.choice(directions)

    return {
        'move': direction,
        'taunt': 'battlesnake-python!'
    }



# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug = True)

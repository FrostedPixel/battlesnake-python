import bottle
import os
import random
import numpy
from Queue import PriorityQueue

# Constants
xpos, ypos = 0,1

CELL_VALUES = {
        'wall': -1,
        'empty': 0,
        'slow': 5,
        'food': 10
    }

DIRECTIONS = {
        'ortho':[(0,1),(1,0),(0,-1),(-1,0)],
        'diag':[(1,1),(-1,-1),(1,-1),(-1,1)]
    }

symbols = {
    'defaultCost':1,
    'starveTrigger':25,
    }

# Classes
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

    def testInBounds(self, pos):
        return (pos[xpos] in range(0,self.width)) and (pos[ypos] in range(0,self.height))

    def toString():
        output = ""
        for r in board:
            for c in r:
                 output += str(c).zfill(2)
            output += '\n'
        return output

class cSnake():
    _map = {}
    def __init__(self, s):
        self._map['id'] = s['id']
        self._map['health'] = s['health']
        self._map['length'] = s['length']
        self._map['name'] = s['name']
        self._map['body'] = [(p['x'],p['y']) for p in s['body']['data']]
        self._map['head'] = self._map['body'][0]
        self._map['tail'] = self._map['body'][-1]
        
    def __getitem__(self, key):
        return self._map[key]
        

# Helper functions
def closeToWall(board, pos, thresh):
    return pos[xpos] - thresh <= 0 or \
           pos[ypos] - thresh <= 0 or \
           pos[xpos] + thresh > board.width  + 1 or \
           pos[ypos] + thresh > board.height + 1

def clampValue(val, min, max):
    if val < min:
        return min
    if val > max:
        return max
    return val

def printDic(dic):
    for key,value in dic.items():
        print "key " + str(key) + " : val " + str(value)

def processChallengers(challengers):
    livingSnakes = []
    for snake in challengers:
        if snake['health'] > 0:
            livingSnakes.append(cSnake(snake))
    return livingSnakes

def listOpenSpaces(board, snake, targets):
    outList = []
    for target in targets:
        candidate = numpy.add(snake, target)
        if board.testInBounds(candidate) and board[candidate.x][candidate.y] != CELL_VALUES['wall']:
            outList.append(candidate)
    return outList

def placeHalo(board, snake, targets, val):
    for target in targets:
        candidate = numpy.add(snake, target)
        candidate = (clampValue(candidate[xpos], 0, board.width - 1), clampValue(candidate[ypos], 0, board.height - 1))
        if (snake == candidate):
            continue
        board[candidate[xpos]][candidate[ypos]] = val

def shortestPath(obstacles, travelWeights, startPoint, endPoint, earlyReturn = False):
    distScore = [[abs(i - startPoint[xpos])+abs(j - startPoint[ypos]) for i in range(obstacles.width)] for j in range(obstacles.height)]

    cameFrom = {}
    costSoFar = {}
    cameFrom[endPoint] = None

    costSoFar[endPoint] = 0
    openList = PriorityQueue()
    openList.put(endPoint, 0)

    while not openList.empty():
        currentPoint = openList.get()
        if earlyReturn and currentPoint == startPoint:
            break
        for dir in DIRECTIONS['ortho']:
            x = currentPoint[xpos]+dir[xpos]
            y = currentPoint[ypos]+dir[ypos]
            nextPoint = (x, y)
            if not (travelWeights.testInBounds(nextPoint) and obstacles.testInBounds(nextPoint)):
                continue
            newCost = costSoFar[currentPoint] + travelWeights[x][y]
            if (obstacles[x][y] != CELL_VALUES['wall'] or nextPoint == startPoint) and (nextPoint not in costSoFar or newCost < costSoFar[nextPoint]):
                costSoFar[nextPoint] = newCost
                openList.put(nextPoint, newCost + distScore[x][y])
                cameFrom[nextPoint] = currentPoint
    return cameFrom

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

    head_url = '%s://%s/static/snake.jpeg' % (
                bottle.request.urlparts.scheme,
                bottle.request.urlparts.netloc
            )
    
    return {
        'color': '#00FF00',
        'taunt': 'Where\'s the food?',
        'head_url': head_url,
        'head_type': 'smile',
        'tail_type': 'regular'
    }

@bottle.post('/end')
def end():
    return "ack"

@bottle.post('/move')
def move():
    movementOptions = {(0,-1):'up', (0,1):'down', (-1,0):'left', (1,0):'right'}
    foodList = []
    preyList = []

    data = bottle.request.json
    ourSnake = cSnake(data['you'])
    
    # get challengers, and remove dead opponents
    challengers = processChallengers(data['snakes']['data'])
    
    # generate board, and fill with movement cost of '1'
    obstacleMap = [[CELL_VALUES['empty'] for x in range(int(data['width']))] for y in range(int(data['height']))]
    obstacleMap = cBoard(obstacleMap)
    travelMap = [[symbols['defaultCost'] for x in range(int(data['width']))] for y in range(int(data['height']))]
    travelMap = cBoard(travelMap)

    # Add food to obstacleMap
    for food in data['food']['data']:
        foodLocation = (food['x'], food['y'])
        if (ourSnake['health'] <= symbols['starveTrigger']) or (not closeToWall(obstacleMap, foodLocation, 2)):
            foodList.append(foodLocation)
            obstacleMap[food['x']][food['y']] = CELL_VALUES['food']

    for snake in challengers:
        snakeGrowth = False
        # mark challengers as 'walls' on obstacleMap and place warnings around larger snakes heads
        if (snake['id'] != ourSnake['id']) and (snake['length'] >= ourSnake['length']):
            placeHalo(travelMap,snake['head'],DIRECTIONS['diag'],CELL_VALUES['slow'])
            placeHalo(obstacleMap,snake['head'],DIRECTIONS['ortho'],CELL_VALUES['wall'])
        # mark challengers as 'food' if they are smaller than us
        if (snake['length'] < ourSnake['length']):
            if closeToWall(obstacleMap, snake['head'], 2):
                continue
            for potentialHead in listOpenSpaces(obstacleMap, snake['head'], DIRECTIONS['ortho']):
                preyList.append(potentialHead)
        # Check if there is food within one cell of a snakes head
        for candidate in DIRECTIONS['ortho']:
            testPt = numpy.add(snake['head'], candidate)
            if not (obstacleMap.testInBounds(testPt)):
                continue
            if (obstacleMap[testPt[xpos]][testPt[ypos]] == CELL_VALUES['food']):
                snakeGrowth =  True
        # Avoid snake tail if they may grow this turn
        for segment in snake['body']:
            if ((segment == snake['tail']) and (not snakeGrowth)):
                continue
            # Draw body segments as walls
            if obstacleMap.testInBounds(segment):
                obstacleMap[segment[xpos]][segment[ypos]] = CELL_VALUES['wall']

    # If we are hunting add prey to food list
    if (ourSnake['health'] > symbols['starveTrigger']) and (not closeToWall(obstacleMap, ourSnake['head'], 2)):
        foodList.append(prey)

    # Find nearest food/prey to our head
    if foodList:
        target = foodList[0]
        distanceToFood = numpy.linalg.norm(target - ourSnake['head'])
        for food in foodList:
            currentDistance = numpy.linalg.norm(food - ourSnake['head'])
            if (currentDistance < distanceToFood):
                distanceToFood = currentDistance
                target = food
    # If foodList is empty, provide all the food as an option (does not handle no-food games)
    else:
        for food in data['food']['data']:
            foodLocation = (food['x'], food['y'])
            foodList.append(foodLocation)

    # find shortest path to food
    path = shortestPath(obstacleMap, travelMap, ourSnake['head'], endPoint, False)
    # direction = random.choice(movementOptions)

    # Check if a path was found, and set first move to a tile adjacent to head
    firstMove = (0, 1)
    if ourSnake['head'] in path:
        firstMove = path[ourSnake['head']]
    # If a path was not found pick open space around head
    else:
        firstMove = listOpenSpaces(obstacleMap, ourSnake['head'], DIRECTIONS['ortho'])[0]

    nextMove = numpy.sub(firstMove, ourSnake['head'])
    if nextMove in movementOptions:
        dirToMove = movementOptions[nextMove]
    else:
        print "Uhoh key not in movementOptions we gonna die"
        dirToMove = 'right'

    return {
        'move': dirToMove,
        'taunt': "Kept you waiting huh?"
    }

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug = True)

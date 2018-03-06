import bottle
import os
import random
import numpy
from Queue import PriorityQueue
from operator import itemgetter

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
    'defCost':1,
    'HuntThresh':25,
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

def removeDeadChallengers(challengers):
    livingSnakes = []
    for snake in challengers:
        if snake['health'] > 0:
            livingSnakes.append(snake)
    return livingSnakes

def genOpenSpacesAroundHead(board, snake, targets):
    outList = []
    for target in targets:
        candidate = (snake[xpos] + target[xpos], snake[ypos] + target[ypos])
        if board.testInBounds(candidate) and board[candidate.x][candidate.y] != CELL_VALUES['wall']:
            outList.append(candidate)
    return outList

def placeHalo(board, snake, targets, val):
    for target in targets:
        candidate = (clampValue(snake[xpos] + target[xpos], 0, board.width - 1), clampValue(snake[ypos] + target[ypos], 0, board.height - 1))
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
        for dir in DIRECTIONS['ortho'])
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
    data = bottle.request.json
    movementOptions = {(0,-1):'up', (0,1):'down', (-1,0):'left', (1,0):'right'}

    you = data['you']
    startPoint = (you['body']['data'][0]['x'], you['body']['data'][0]['y'])

    # generate board, and fill with movement cost of '1'
    obstacleMap = [[CELL_VALUES['empty'] for x in range(int(data['width']))] for y in range(int(data['height']))]
    obstacleMap = cBoard(obstacleMap)
    travelMap = [[symbols['defCost'] for x in range(int(data['width']))] for y in range(int(data['height']))]
    travelMap = cBoard(travelMap)

    # get challengers, and remove dead opponents
    challengers = data['snakes']['data']
    challengers = removeDeadChallengers(challengers)

    foodList = []

    # mark challengers as 'walls' on obstacleMap
    for snake in challengers:
        snakePos = (snake['body']['data'][0]['x'], snake['body']['data'][0]['y'])
        if (snake['id'] != you['id']) and (snake['length'] >= you['length']):
            placeHalo(travelMap,snakePos,DIRECTIONS['diag'],CELL_VALUES['slow'])
            placeHalo(obstacleMap,snakePos,DIRECTIONS['ortho'],CELL_VALUES['wall'])

    # Add food to obstacleMap
    for food in data['food']['data']:
        foodLocation = (food['x'], food['y'])
        if (you['health'] <= symbols['HuntThresh']) or (not closeToWall(obstacleMap, foodLocation, 2)):
            foodList.append(foodLocation)
        # TODO: remove? not used
        obstacleMap[food['x']][food['y']] = CELL_VALUES['food']
        print "[{}][{}]\n".format(food['x'], food['y'])
    if not foodList:
        for food in data['food']['data']:
            foodLocation = (food['x'], food['y'])
            foodList.append(foodLocation)

    for snake in challengers:
        snakeGrowth = False
        snakePos = (snake['body']['data'][0]['x'], snake['body']['data'][0]['y'])
        for candidate in DIRECTIONS['ortho']:
            testPt = (snakePos[xpos] + candidate[xpos], snakePos[ypos] + candidate[ypos])
            if not (obstacleMap.testInBounds(testPt)):
                continue
            if (obstacleMap[snakePos[xpos] + candidate[xpos]][snakePos[ypos] + candidate[ypos]] == CELL_VALUES['food']):
                snakeGrowth =  True
        for segment in snake['body']['data']:
            if ((segment == snake['body']['data'][-1]) and (not snakeGrowth)):
                continue
            wallPt = (segment['x'], segment['y'])
            if obstacleMap.testInBounds(wallPt):
                obstacleMap[wallPt[xpos]][wallPt[ypos]] = CELL_VALUES['wall']

    if (you['health'] > symbols['HuntThresh']) and (not closeToWall(obstacleMap, startPoint, 2)):
        for snake in challengers:
            if (snake['length'] < you['length']):
                snakePos = (snake['body']['data'][0]['x'], snake['body']['data'][0]['y'])
                if closeToWall(obstacleMap, snakePos, 2):
                    continue
                for potentialHead in genOpenSpacesAroundHead(obstacleMap, snakePos, DIRECTIONS['ortho']):
                    foodList.append(potentialHead)

    if foodList:
        endPoint = foodList[0]
        distanceToFood = (abs(endPoint[xpos] - startPoint[xpos]) + abs(endPoint[ypos] - startPoint[ypos]))
        for food in foodList:
            currentDistance = (abs(startPoint[xpos] - food[xpos]) + abs(startPoint[ypos] - food[ypos]))
            if (currentDistance < distanceToFood):
                distanceToFood = currentDistance
                endPoint = food

    # find shortest path to food
    path = shortestPath(obstacleMap, travelMap, startPoint, endPoint, False)
    # direction = random.choice(movementOptions)

    firstSquare = (0, 1)
    if startPoint in path:
        firstSquare = path[startPoint]
    else:
        for direc in DIRECTIONS['ortho']:
            potential = (startPoint[xpos] + direc[xpos], startPoint[ypos] + direc[ypos])
            if obstacleMap.testInBounds(potential) and obstacleMap[potential[xpos]][potential[ypos]] != CELL_VALUES['wall']:
                firstSquare = potential

    squareToMoveTo = numpy.sub(firstSquare, startPoint)
    if squareToMoveTo in movementOptions:
        dirToMove = movementOptions[squareToMoveTo]
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

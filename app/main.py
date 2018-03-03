import bottle
import os
import random
import operator

symbols = {
    'walls':-1,
    'empty':0,
    'tough':5,
    'food':10,
    }

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

def removeDeadChallengers(challengers):
    livingSnakes = []
    for snake in challengers:
        if snake['health'] > 0:
            livingSnakes.append(snake)
    return livingSnakes

def shortestPath(board, startPoint, endPoint):
    distScore = [[abs(i - startPoint.x)+abs(j - startPoint.y) for i in range(len(board[0]))] for j in range(len(board[0][0]))]

    cameFrom = {}
    costSoFar = {}
    cameFrom[endPoint] = None

    costSoFar[endPoint] = 0
    openList = PriorityQueue()
    openList.put(endPoint, 0)

    iters = 0

    while not openList.empty():
        iters += 1

        currentPoint = openList.get()
        for dir in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            x = clamp(currentPoint.x+dir[0], 0, 9)
            y = clamp(currentPoint.y+dir[1], 0, 9)
            nextPoint = point(x, y)
            newCost = costSoFar[currentPoint] + board[x][y]
            if board[x][y] != WALL and (nextPoint not in costSoFar or newCost < costSoFar[nextPoint]):
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
        'taunt': 'Where is the food?',
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
    startPoint = point((you['body']['data']['x'],you['body']['data']['y']))

    # generate board, and fill with movement cost of '1'
    board = [[1 for x in range(data['width'])] for y in range(['height'])]

    # get challengers, and remove dead opponents
    challengers = data['snakes']['data']
    challengers = removeDeadChallengers(challangers)

    # mark challengers as 'walls' on board
    for snake in challengers:
        if (snake['id'] != you['id']) and (snake['length'] >= you['length']):
            for wall in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                board[snake.x + wall.x][snake.y + wall.y] = symbols['wall']
            for tough in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
                board[snake.x + wall.x][snake.y + wall.y] = symbols['tough']
        for segment in snake['body']['data']:
            board[segment['x']][segment['y']] = symbols['wall']

    # find nearest food
    endPoint = point((data['food']['data']['x'],data['food']['data']['y']))
    distanceToFood = abs(endPoint - startPoint)
    for food in data['food']['data']:
        currentDistance = abs(endPoint - point((food['data']['x'],food['data']['y'])))
        if (currentDistance < distanceToFood):
            distanceToFood = currentDistance
            endPoint = food

    # find shortest path to food
    path = shortestPath(board, startPoint, endPoint)

    # direction = random.choice(directions)

    return {
        'move': directions[point(path[0].x - startPoint.x, path[0].y - startPoint.y)],
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

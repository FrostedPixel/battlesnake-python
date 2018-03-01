import bottle
import os
import random
import numpy

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

import json

from channels import Group

from .models import Game, PlayerAction, gm, reset_game

def ws_add(message):
    message.reply_channel.send({'accept': True})
    Group('players').add(message.reply_channel)

def ws_disconnect(message):
    Group('players').discard(message.reply_channel)

def ws_message(message):
    request_data = json.loads(message.content['text'])
    response_data = {}
    if request_data['action'] == 'new_game':
        reset_game(request_data['difficulty'])
        response_data['game_data'] = gm.dump()
        response_data['action'] = 'construct'
    elif request_data['action'] == 'reveal':
        tile_index = int(request_data['tile_index'])
        response_data['game_data'] = gm.reveal(tile_index)
        response_data['action'] = 'update'
    elif request_data['action'] == 'toggle_flag':
        tile_index = int(request_data['tile_index'])
        response_data['game_data'] = gm.toggle_flag(tile_index)
        response_data['action'] = 'update'
    elif request_data['action'] == 'undo':
        response_data['game_data'] = gm.undo()
        response_data['action'] = 'update'
    Group('players').send({'text': json.dumps(response_data)})

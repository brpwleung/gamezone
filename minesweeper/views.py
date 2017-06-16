import json
import random

from channels import Group

from django.http import HttpResponse
from django.shortcuts import render

from .models import gm, reset_game

def index(request):
    return render(request, 'minesweeper/index.html')

def new_game(request):
    """AJAX request handler to invoke a new game instance."""

    request_data = json.loads(request.POST['json'])
    reset_game(request_data['difficulty'])
    response_data = {
        'action': 'construct',
        'game_data': gm.dump(),
        }
    Group('players').send({'text': json.dumps(response_data)})
    return HttpResponse()

def restore(request):
    """AJAX request handler to fetch the current game state."""

    response_data = gm.dump()
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
        )

def reveal(request):
    """AJAX request handler for a tile reveal action."""

    request_data = json.loads(request.POST['json'])
    response_data = {
        'action': 'update',
        'game_data': gm.reveal(int(request_data['id'])),
        }
    Group('players').send({'text': json.dumps(response_data)})
    return HttpResponse()

def toggle_flag(request):
    """AJAX request handler to flag/unflag a game tile."""

    request_data = json.loads(request.POST['json'])
    response_data = {
        'action': 'update',
        'game_data': gm.toggle_flag(int(request_data['id'])),
        }
    Group('players').send({'text': json.dumps(response_data)})
    return HttpResponse()

reset_game()

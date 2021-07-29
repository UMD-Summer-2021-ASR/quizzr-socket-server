from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import game
import lobby
import string
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '3ca170251cc76400b62d4f4feb73896c5ee84ebddabf5e82'
socketio = SocketIO(app, cors_allowed_origins="*")
live_game = None

lobbies = {}
games = {}


def id_generator(size=4, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@app.route('/')
def sessions():
    return render_template('session.html')


@socketio.on('startlobby')
def start_lobby(json, methods=['GET', 'POST']):
    lobbycode = id_generator(4)
    lobbies[lobbycode] = lobby.Lobby(json['username'], lobbycode)
    join_room(lobbycode)
    print("Lobby started. Code: " + lobbycode)
    emit('lobbystate', lobbies[lobbycode].state(), to=lobbycode)


@socketio.on('joinlobby')
def join_lobby(json, methods=['GET', 'POST']):
    lobbies[json['lobby']].join(json['username'])
    join_room(json['lobby'])
    emit('lobbystate', lobbies[json['lobby']].state(), to=json['lobby'])


@socketio.on('leavelobby')
def leave_lobby(json, methods=['GET', 'POST']):
    leave_room(json['lobby'])
    lobbies[json['lobby']].leave(json['username'])
    emit('lobbystate', lobbies[json['lobby']].state(), to=json['lobby'])


@socketio.on('startgame')
def start_game(json, methods=['GET', 'POST']):
    print("Game started in lobby " + json['lobby'])
    games[json['lobby']] = game.Game()
    emit('gamestarted', to=json['lobby'])


@socketio.on('getstate')
def get_state(json, methods=['GET', 'POST']):
    print(games[json['lobby']].gamestate())
    emit('gamestate', games[json['lobby']].gamestate(), to=json['lobby'])


@socketio.on('buzz')
def buzz(json, methods=['GET', 'POST']):
    games[json['lobby']].buzz(json['username'])
    emit('buzzed', json['username'], to=json['lobby'])


@socketio.on('answer')
def answer(json, methods=['GET', 'POST']):
    emit('answered', games[json['lobby']].answer(json['username'], json['answer']), to=json['lobby'])


if __name__ == '__main__':
    socketio.run(app, debug=True)

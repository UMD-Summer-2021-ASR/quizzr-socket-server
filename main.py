from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque
import game
import lobby
import random
import asyncio
from firebase_admin import auth, initialize_app
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '';
app = Flask(__name__)
firebase_app = initialize_app()
app.config['SECRET_KEY'] = '3ca170251cc76400b62d4f4feb73896c5ee84ebddabf5e82'
socketio = SocketIO(app, cors_allowed_origins="*")
live_game = None

current_lobby = {}  # UID : room name
lobbies = {}  # room name : lobby object
games = {}  # room name : game object
queues = {
    "casualsolo": deque([]),
    "casualduo": deque([]),
    "rankedsolo": deque([]),
    "rankedduo": deque([]),
}
loop = asyncio.get_event_loop()


def lobbycode_generator(size=4, chars='ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'):
    return ''.join(random.choice(chars) for _ in range(size))


@app.route('/')
def sessions():
    return render_template('session.html')


@socketio.on('startlobby')  # starts a lobby and makes user join
def start_lobby(json, methods=['GET', 'POST']):
    # TODO CHECK FIREBASE ID
    decoded_token = auth.verify_id_token(json['auth'])
    print(decoded_token)

    lobbycode = lobbycode_generator(4)
    while lobbycode in lobbies:
        lobbycode = lobbycode_generator(4)
    lobbies[lobbycode] = lobby.Lobby(json['username'], lobbycode, 0, 8)
    join_room(lobbycode)
    current_lobby[json['username']] = lobbycode
    print("Lobby started. Code: " + lobbycode)
    emit('alert', ['success', 'Started lobby ' + lobbycode])

    async def periodic():
        while True:
            emit('lobbystate', lobbies[lobbycode].state(), to=lobbycode)
            await asyncio.sleep(1)

    try:
        loop.run_until_complete(periodic())
    except asyncio.CancelledError:
        pass


@socketio.on('lobbystate')
def get_lobby(json, methods=['GET', 'POST']):
    if not (json['lobby'] in lobbies):
        emit('alert', ['error', 'Lobby ' + str(json['lobby']) + ' does not exist'])
        return
    emit('lobbystate', lobbies[json['lobby']].state())


@socketio.on('joinlobby')  # if lobby with given code exists, join it. otherwise, alert failed
def join_lobby(json, methods=['GET', 'POST']):
    if not (json['lobby'] in lobbies):
        emit('alert', ['error', 'Lobby ' + str(json['lobby']) + ' does not exist'])
        return
    if lobbies[json['lobby']].join(json['username']):
        join_room(json['lobby'])
        emit('alert', ['success', 'Joined lobby ' + str(json['lobby'])])
        emit('alert', ['success', str(json['username']) + ' joined the lobby'], include_self=False, to=json['lobby'])
        emit('lobbystate', lobbies[json['lobby']].state(), to=lobby)
    else:
        emit('alert', ['error', 'Lobby ' + str(json['lobby']) + ' is full'])


@socketio.on('leavelobby')
def leave_lobby(json, methods=['GET', 'POST']):
    leave_room(json['lobby'])
    lobbies[json['lobby']].leave(json['username'])
    emit('alert', ['show', str(json['username']) + ' left the lobby'], to=json['lobby'])


@socketio.on('startgame')
def start_game(json, methods=['GET', 'POST']):
    # Start game with correct lobby parameters according to key
    print("Game started in lobby " + json['lobby'])
    games[json['lobby']] = game.Game(json['players'])
    emit('gamestarted', {}, to=json['lobby'])


@socketio.on('gamestate')
def get_state(json, methods=['GET', 'POST']):
    # print(games[json['lobby']].gamestate())
    emit('gamestate', games[json['lobby']].gamestate())


@socketio.on('buzz')
def buzz(json, methods=['GET', 'POST']):
    games[json['lobby']].buzz(json['username'])
    emit('buzzed', json['username'], to=json['lobby'])


@socketio.on('answer')
def answer(json, methods=['GET', 'POST']):
    emit('answered', games[json['lobby']].answer(json['username'], json['answer']), to=json['lobby'])


if __name__ == '__main__':
    socketio.run(app, debug=True, port=4000)

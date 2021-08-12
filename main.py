from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque
import game
import lobby
import random
import asyncio
from nonsocketfunctions import lobbycode_generator, cache_user, get_user
from firebase_admin import auth, initialize_app
import os
import threading
import requests

os.environ[
    'GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/andrewchen/PycharmProjects/quizzr-socket-server/secrets/quizzrio-firebase-adminsdk-m39pr-6e4a9cfa44.json';
app = Flask(__name__)
firebase_app = initialize_app()
app.config['SECRET_KEY'] = '3ca170251cc76400b62d4f4feb73896c5ee84ebddabf5e82'
socketio = SocketIO(app, cors_allowed_origins="*")
live_game = None

current_lobby = {}  # UID : room name
usernames = {} # UID : username
lobbies = {}  # room name : lobby object
games = {}  # room name : game object
queues = {
    "casualsolo": deque([]),
    "casualduo": deque([]),
    "rankedsolo": deque([]),
    "rankedduo": deque([]),
}
test_data = [0]


async def emitstate(sleep_time=0.1):
    while True:
        for lobbycode in lobbies:
            socketio.emit('lobbystate', lobbies[lobbycode].state(), to=lobbycode)
        for gamecode in games:
            socketio.emit('gamestate', games[gamecode].gamestate(), to=gamecode)
        await asyncio.sleep(sleep_time)


@app.route('/')
def sessions():
    return render_template('session.html')


@socketio.on('startlobby')  # starts a lobby and makes user join
def start_lobby(json, methods=['GET', 'POST']):
    cache_user(json['auth'])
    user = get_user(json['auth'])
    username = user['username']

    lobbycode = lobbycode_generator(6)
    while lobbycode in lobbies:
        lobbycode = lobbycode_generator(6)
    lobbies[lobbycode] = lobby.Lobby(username, lobbycode, 0, 8)
    join_room(lobbycode)
    current_lobby[username] = lobbycode
    print("Lobby started. Code: " + lobbycode)
    emit('alert', ['success', 'Started lobby ' + lobbycode])


@socketio.on('joinlobby')  # if lobby with given code exists, join it. otherwise, alert failed
def join_lobby(json, methods=['GET', 'POST']):
    cache_user(json['auth'])
    user = get_user(json['auth'])
    username = user['username']
    lobbycode = json['lobby']

    if not (lobbycode in lobbies):
        emit('alert', ['error', 'Lobby ' + str(lobbycode) + ' does not exist'])
        return
    if lobbies[lobbycode].join(username):
        current_lobby[username] = lobbycode
        join_room(lobbycode)
        emit('alert', ['success', 'Joined lobby ' + str(lobbycode)])
        emit('alert', ['success', str(username) + ' joined the lobby'], include_self=False, to=lobbycode)
    else:
        emit('alert', ['error', 'Lobby ' + str(lobbycode) + ' is full'])


@socketio.on('leavelobby')
def leave_lobby(json, methods=['GET', 'POST']):
    user = get_user(json['auth'])
    lobby = current_lobby[user['username']]
    username = user['username']

    leave_room(lobby)
    lobbies[lobby].leave(username)
    emit('alert', ['show', str(username) + ' left the lobby'], to=lobby)


@socketio.on('startgame')
def start_game(json, methods=['GET', 'POST']):
    # Start game with correct lobby parameters according to key
    user = get_user(json['auth'])
    lobby = current_lobby[user['username']]

    print("Game started in lobby " + lobby)
    games[lobby] = game.Game(lobbies[lobby].players)
    emit('gamestarted', {}, to=lobby)


@socketio.on('buzz')
def buzz(json, methods=['GET', 'POST']):
    user = get_user(json['auth'])
    lobby = current_lobby[user['username']]
    username = user['username']

    buzzed = games[lobby].buzz(username)
    if buzzed:
        emit('buzzed', username, to=lobby)
    else:
        emit('alert', ['error', "You can't buzz right now"])


@socketio.on('answer')
def answer(json, methods=['GET', 'POST']):
    user = get_user(json['auth'])
    username = user['username']
    lobby = current_lobby[user['username']]

    answered = games[lobby].answer(username, json['answer'])
    if answered:
        emit('answered', {}, to=lobby)
    else:
        emit('alert', ['error', "You can't answer right now"])



def run_socketio():
    socketio.run(app, port=4000)


def run_asyncio():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(emitstate())
    loop.run_forever()


if __name__ == '__main__':
    socket_thread = threading.Thread(target=run_socketio)
    asyncio_thread = threading.Thread(target=run_asyncio)
    socket_thread.start()
    asyncio_thread.start()

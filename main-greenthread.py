import eventlet

eventlet.monkey_patch()

import os

###
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
###

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room
from collections import deque
import game
import lobby
import random
from nonsocketfunctions import lobbycode_generator, cache_user, get_user
from firebase_admin import auth, initialize_app


import threading
import requests
import time
import json
import string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
firebase_app = initialize_app()
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*")

# SHARED BETWEEN THREADS
current_lobby = {}  # UID : room name
usernames = {}  # UID : username
uids = {}  # username : UID
lobbies = {}  # room name : lobby object
games = {}  # room name : game object
previous_gamestate = {}  # room name : game object (used for catching when to send next question
clients = {}  # sid : username
queues = {
    "casualsolo": deque([]),
    "casualduo": deque([]),
    "rankedsolo": deque([]),
    "rankedduo": deque([]),
}


# SHARED BETWEEN THREADS


def emit_game_state(
    sleep_time=0.1,
):  # emits the game state (time left on clock, who is buzzing, time remaining in
    # the buzz, points, etc.)
    while True:
        for gamecode in games:
            gamestate = games[gamecode].gamestate()
            if gamecode in previous_gamestate:
                if previous_gamestate[gamecode][2] != gamestate[2]:
                    games[gamecode].get_new_question()
            else:
                games[gamecode].get_new_question()
                # socketio.emit('newquestion', games[gamecode].get_new_question(), to=gamecode)
            socketio.emit("gamestate", games[gamecode].gamestate(), to=gamecode)
            previous_gamestate[gamecode] = gamestate
        eventlet.sleep(sleep_time)


def emit_lobby_state(
    sleep_time=0.1,
):  # emits the lobby state (synchronizes lobby settings between all players in the lobby)
    while True:
        for lobbycode in lobbies:
            socketio.emit("lobbystate", lobbies[lobbycode].state(), to=lobbycode)
        eventlet.sleep(sleep_time)


# TODO fix with UID support
def clean_lobbies_and_games(
    sleep_time=30,
):  # cleans dead lobbies and games (0 players, game ended, etc.)
    while True:
        current_time = time.time()
        for lobbycode in list(lobbies):
            if current_time - lobbies[lobbycode].start_time > 600 and not lobbies[lobbycode].game_started:
                socketio.emit("closelobby", {}, to=lobbycode)
                socketio.emit("alert", ["error", "Lobby closed due to inactivity"], to=lobbycode)
                players_list = lobbies[lobbycode].get_players_list()
                for player in players_list:
                    current_lobby.pop(player, None)
                lobbies.pop(lobbycode, None)
                socketio.close_room(lobbycode)
                print("Closed lobby " + str(lobbycode) + " due to inactivity")
        for gamecode in list(games):
            if not games[gamecode].active_game:
                lobbies.pop(gamecode, None)
                games.pop(gamecode, None)
                print("Closed game " + str(gamecode))
        eventlet.sleep(sleep_time)


@app.route("/")
def sessions():
    return render_template("session.html")


# Socket endpoint for sending all users in a lobby to the lobby loading screen while the streams are created
@socketio.on("lobbyloading")  # makes user in lobby go to loading screen
def lobby_loading(json, methods=["GET", "POST"]):
    user = get_user(json["auth"])
    lobby = current_lobby[user["username"]]
    username = user["username"]
    emit("lobbyloading", {}, to=lobby)


# Socket endpoint for starting a lobby
@socketio.on("startlobby")  # starts a lobby and makes user join
def start_lobby(json, methods=["GET", "POST"]):
    cache_user(json["auth"])
    user = get_user(json["auth"])
    username = user["username"]

    clients[request.sid] = username
    lobbycode = lobbycode_generator(6)
    while lobbycode in lobbies:
        lobbycode = lobbycode_generator(6)
    lobbies[lobbycode] = lobby.Lobby(username, lobbycode, json["gamemode"], json["auth"])
    join_room(lobbycode)
    current_lobby[username] = lobbycode
    print("Lobby started. Code: " + lobbycode)
    emit("lobbystate", lobbies[lobbycode].state(), to=lobbycode)
    emit("alert", ["success", "Started lobby " + lobbycode])


# Socket endpoint for joining a lobby
@socketio.on("joinlobby")  # if lobby with given code exists, join it. otherwise, alert failed
def join_lobby(json, methods=["GET", "POST"]):
    cache_user(json["auth"])
    user = get_user(json["auth"])
    username = user["username"]
    lobbycode = json["lobby"]

    clients[request.sid] = username
    if not (lobbycode in lobbies):
        emit("alert", ["error", "Lobby " + str(lobbycode) + " does not exist"])
        return
    if lobbies[lobbycode].join(username):
        current_lobby[username] = lobbycode
        join_room(lobbycode)
        emit("lobbystate", lobbies[lobbycode].state(), to=lobbycode)
        emit("alert", ["success", "Joined lobby " + str(lobbycode)])
        emit(
            "alert",
            ["success", str(username) + " joined the lobby"],
            include_self=False,
            to=lobbycode,
        )
    else:
        emit("alert", ["error", "Lobby " + str(lobbycode) + " is full"])


# Socket endpoint for switching teams
@socketio.on("switchteam")
def switch_team(json, methods=["GET", "POST"]):
    user = get_user(json["auth"])
    lobby = current_lobby[user["username"]]
    x = 5 / 0
    result = lobbies[lobby].switch_team(json["user"])
    if result:
        emit("lobbystate", lobbies[lobby].state(), to=lobby)
        emit("alert", ["success", str(json["user"]) + " switched teams"], to=lobby)
    else:
        emit("alert", ["error", "Switching teams failed"], to=lobby)


# Socket endpoint for updating settings in-game
@socketio.on("updatesettings")
def update_settings(json, methods=["GET", "POST"]):
    user = get_user(json["auth"])
    lobby = current_lobby[user["username"]]

    lobbies[lobby].update_settings(json["settings"])
    emit("lobbystate", lobbies[lobby].state(), to=lobby)


# Socket endpoint for leaving a lobby
@socketio.on("leavelobby")
def leave_lobby(json, methods=["GET", "POST"]):
    user = get_user(json["auth"])
    lobby = current_lobby[user["username"]]
    username = user["username"]

    leave_room(lobby)
    lobbies[lobby].leave(username)
    emit("lobbystate", lobbies[lobby].state(), to=lobby)
    emit("alert", ["show", str(username) + " left the lobby"], to=lobby)


# Socket endpoint for starting a game from a lobby
@socketio.on("startgame")
def start_game(json, methods=["GET", "POST"]):
    # Start game with correct lobby parameters according to key
    user = get_user(json["auth"])
    lobby = current_lobby[user["username"]]

    single_game = game.Game(lobbies[lobby], socketio)
    if single_game.good_game:
        games[lobby] = single_game
        print("Game started in lobby " + lobby)
        lobbies[lobby].game_started = True
        emit("gamestarted", {}, to=lobby)


# Socket endpoint for buzzing in game
@socketio.on("buzz")
def buzz(json, methods=["GET", "POST"]):
    user = get_user(json["auth"])
    lobby = current_lobby[user["username"]]
    username = user["username"]

    buzzed = games[lobby].buzz(username)
    if buzzed:
        emit("buzzed", username, to=lobby)
    else:
        emit("alert", ["error", "You can't buzz right now"])


# Socket endpoint for answering by text
@socketio.on("answer")
def answer(json, methods=["GET", "POST"]):
    user = get_user(json["auth"])
    username = user["username"]
    lobby = current_lobby[user["username"]]

    answered = games[lobby].answer(username, json["answer"])
    if not answered:
        emit("alert", ["error", "You can't answer right now"])


# Socket endpoint for classifier results
@socketio.on("audioanswer")
def audioanswer(json, methods=["GET", "POST"]):
    user = get_user(json["auth"])
    username = user["username"]
    lobby = current_lobby[user["username"]]

    answered = games[lobby].classifier_answer(username, json["filename"])
    if not answered:
        emit("alert", ["error", "You can't answer right now"])


# TODO broken for some reason?
# @socketio.on('disconnect')
# def user_disconnected():
#     username = clients[request.sid]
#     lobby = current_lobby[username]
#
#     leave_room(lobby)
#     lobbies[lobby].leave(username)
#     emit('lobbystate', lobbies[lobby].state(), to=lobby)
#     emit('alert', ['show', str(username) + ' left the lobby'], to=lobby)


@app.route("/audioanswerupload", methods=["POST"])
def audioanswerupload():
    user = get_user(request.form.get("auth"))
    username = user["username"]
    lobby = current_lobby[user["username"]]

    # get qid
    current_game = games[lobby]
    qid = current_game.answering_ids[current_game.round - 1][current_game.question - 1]

    # upload file and get filename
    file = request.files["audio"]
    filename = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20)) + ".wav"
    while os.path.exists("./answer-audios/" + filename):
        filename = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20)) + ".wav"

    file.save(os.path.join("./answer-audios", filename))
    file.close()

    # response
    response = jsonify({"filename": filename})
    return response


# Runs the flask socketio server
def run_socketio():
    pass


# Runs the flask server
# def run_flask():
#     app.run(port=int(os.environ.get("SOCKET_FLASK_PORT")), host="0.0.0.0")


# # Runs the asyncio tasks permanently (game state, lobby state, cleaning dead lobbies and games)
# def run_asyncio():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.create_task(
#         emit_game_state())  # emits the game state (time left on clock, who is buzzing, time remaining in the buzz, points, etc.)
#     loop.create_task(
#         emit_lobby_state())  # emits the lobby state (synchronizes lobby settings between all players in the lobby)
#     loop.create_task(clean_lobbies_and_games())  # cleans dead lobbies and games (0 players, game ended, etc.)
#     loop.run_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the socket server", add_help=True)
    parser.add_argument(
        "--socketport",
        dest="socketport",
        type=int,
        help="The host name to use for the server",
        default=6470,
    )
    parser.add_argument(
        "--secretpath",
        dest="secretpath",
        type=str,
        help="The host name to use for the server",
        default="/fs/clip-quiz/saptab1/ASRQA/Interface/quizzr-socket-server/quizzr.json",
    )
    parser.add_argument(
        "--handshake",
        dest="handshake",
        type=str,
        help="The host name to use for the server",
        default="I-AM-A-SECRET-KEY",
    )
    args = parser.parse_args()
    print(args)
    os.environ["HLS_HANDSHAKE"] = args.handshake
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.secretpath
    os.environ["HLS_URL"] = "http://localhost:4440"
    os.environ["BACKEND_URL"] = "http://localhost:5110"
    eventlet.spawn(emit_game_state)
    eventlet.spawn(emit_lobby_state)
    eventlet.spawn(clean_lobbies_and_games)
    socketio.run(app, port=int(args.socketport), host="0.0.0.0", log_output=True)

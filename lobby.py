class Lobby:
    def __init__(self, initial_player, code):
        self.players = [initial_player]
        self.code = code

    def state(self):
        return [self.players, self.code]

    def leave(self, username):
        self.players.remove(username)

    def join(self, username):
        self.players.append(username)
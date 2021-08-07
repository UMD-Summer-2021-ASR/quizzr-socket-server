class Lobby:
    def __init__(self, initial_player, code, teams, max_players):
        self.players = [initial_player]  # List of players
        self.code = code  # Room code
        self.teams = 0  # Number of teams
        self.max_players = 8  # maximum number of players

    # Updates lobby settings
    def update_settings(self, teams, max_players):
        # TODO Clean input
        self.teams = teams
        self.max_players = max_players

    # Returns current lobby state
    def state(self):
        return [self.players, self.code, self.teams, self.max_players]

    # Removes player from lobby
    def leave(self, username):
        self.players.remove(username)

    # Adds player to lobby
    def join(self, username):
        # Check does not exceed max players
        #
        self.players.append(username)

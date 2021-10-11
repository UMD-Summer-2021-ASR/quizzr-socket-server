class Queue:
    def __init__(self, key):
        self.key = key
        self.queue = []
        self.queueSettings = []  # TODO add queue settings to define good match

    # returns if two lobbies are a good match
    def good_match(self, a, b):
        return True

    # greedily finds matches between lobbies in the queue
    # if found, returns them in list
    def find_match(self):
        out = []
        for i in range(len(self.queue)):
            for j in range(i, len(self.queue)):
                if i == j:
                    continue

                if self.good_match(self.queue[i], self.queue[j]):
                    out.append(self.queue[i])
                    out.append(self.queue[j])
                    self.queue.pop(j)
                    self.queue.pop(i)
                    return out

        return out

    # moves a lobby into the queue
    def join(self, lobby):
        if lobby.gamemode != self.key:
            return False

        self.queue.append(lobby)
        return True

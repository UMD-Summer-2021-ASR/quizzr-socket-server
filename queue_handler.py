import time
import rating_handler as rt


def time_elapsed_sigmoid(t, div=60):
    # parameters: t = original time, div = how much to divide the time by (e.g. 60 for a minute)
    elapsed_time = time.time() - t
    return 1 / (1 + 2.71 ** elapsed_time / div)


class Queue:
    def __init__(self, key):
        self.key = key
        self.queue = []  # each element is [username, time in queue]
        self.queueSettings = {
            "max_match_range": 500
        }

    # returns if two lobbies are a good match
    def good_match(self, a, b):
        acceptable_difference_a = self.queueSettings['max_match_range'] * time_elapsed_sigmoid(a[1])
        acceptable_difference_b = self.queueSettings['max_match_range'] * time_elapsed_sigmoid(a[2])

        difference = rt.compare(a[0], a[1])

        return acceptable_difference_a >= difference and acceptable_difference_b >= difference

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

        self.queue.append([lobby, time.time()])
        return True

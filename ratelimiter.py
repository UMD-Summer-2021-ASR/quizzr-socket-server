import time
from collections import deque


class RateLimiter:
    def __init__(self):
        self.calls = {}  # Event key <string> : (UserID <string> : Calls <dequeue<float>>)
        self.limits = {}  # Event key <string> : [Calls <int>, Time (sec) <int>] ie how many calls per time is allowed
        self.settings = {} # Event key <string> : (Setting name <string> : value <?>)

    # Create an event to rate limit at max_calls per unit_time per user
    # event_key must be unique
    def create_event(self, event_key, max_calls=10, unit_time=60, count_invalid_calls=True):
        if event_key in self.limits[event_key]:
            print("Error: Event key '" + event_key +
                  "' already exists. Please use a different key.")
        self.calls[event_key] = {}
        self.limits[event_key] = [max_calls, unit_time]
        # Boolean for if the limiter also log rate-limited calls (and limit based on them for future calls)
        self.settings[event_key] = {'count_invalid_calls':count_invalid_calls}

    # Determine whether an event call is valid (create_event must be used prior to calling valid_call)
    def valid_call(self, event_key, user_id):
        # Print error if event_key doesn't exist
        if not (event_key in self.limits):
            print("Error: Event key '" + event_key +
                  "' does not exist. Create it first using the create_event function.")
            return False

        # If user hasn't called before
        if not (user_id in self.calls[event_key]):
            self.calls[event_key][user_id] = deque([time.time()])
            return True

        # Cleanup previous calls
        current_window = time.time() - self.limits[event_key][1]
        while len(self.calls[event_key][user_id]) > 0 and self.calls[event_key][user_id][0] < current_window:
            self.calls[event_key][user_id].popleft()
        valid = len(self.calls[event_key][user_id])+1 <= self.limits[event_key][0]
        if valid:
            self.calls[event_key][user_id].append(time.time())
        elif (not valid) and self.settings[event_key]['count_invalid_calls']:
            self.calls[event_key][user_id].append(time.time())
        return valid

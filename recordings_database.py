import random


class recordings_database:
    def __init__(self):
        self.recordings = {}
        self.nouns = []
        with open('common_nouns.txt') as f:
            self.nouns = f.readlines()
            self.nouns = [x.strip() for x in self.nouns]

    def get_recording(self, code):
        return self.recordings[code]

    def add_recording(self, recording):
        code = self.get_code()
        self.recordings[code] = recording
        return code

    def get_code(self):
        code = ''.join(map(str, random.sample(self.nouns, 5)))
        while code in self.recordings:
            code = ''.join(map(str, random.sample(self.nouns, 5)))
        return code

    def remove_recording(self, code):
        if code not in self.recordings:
            print('Code ' + str(code) + ' not in recordings database')
            return
        else:
            self.recordings.pop(code)
            print('Code ' + str(code) + ' removed from recordings database')


database = recordings_database()

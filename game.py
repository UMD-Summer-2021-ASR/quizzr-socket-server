import time
import requests
import random
import json

HANDSHAKE = "I-AM-A-SECRET-KEY" # used for HLS

# returns the final time of a VTT string passed in
def get_final_time(vtt):
    return float(vtt.split('\n')[-4].split(':')[-1])

class Game:
    def __init__(self, lobby):
        # TODO Set settings according to game type

        # game settings
        self.gamemode = lobby.gamemode  # game type
        self.rounds_num = lobby.settings['rounds']  # total number of rounds
        self.questions_num = lobby.settings['questions_num']  # questions per round
        self.tiebreaker = 'random'  # method to break ties
        self.buzz_time = 8  # time a player is given to answer after buzzing
        self.post_buzz_time = lobby.settings['post_buzz_time']  # time after a question that a player can still buzz
        self.gap_time = lobby.settings['gap_time']  # time between questions
        self.teams = lobby.settings['teams']
        self.players = lobby.settings['players']
        self.auth_token = lobby.auth_token

        # for game state
        self.active_game = True  # active
        self.active_question = [False, 0]  # active, time started
        self.active_buzz = [False, 0, 0, ""]  # active, time started, question time remaining at buzz, username
        self.active_gap = [True, time.time()]  # active, time started
        self.round = 1  # current round
        self.question = 1  # current question
        self.buzzer = ""  # username of person who buzzed
        self.points = {}
        if self.teams == 0:
            for player in self.players:
                self.points[player] = 0
        else:
            self.points = [{}, {}]
            for player in self.players[0]:
                self.points[0][player] = 0
            for player in self.players[1]:
                self.points[1][player] = 0

        raw_questions = requests.get('http://localhost:5000/question',
                              params={'batchSize': self.questions_num * self.rounds_num},
                              headers={'Authorization': self.auth_token}).json()['results']
        self.questions = [] # id, qb_id, time length
        for question in raw_questions:
            self.questions.append([question['audio'][0]['id'], question['qb_id'], get_final_time(question['audio'][0]['vtt']) + self.post_buzz_time])

        # for storage
        self.date = time.strftime("%Y %m %d %H %M %S", time.gmtime())  # Year month day hour minute second (UTC)
        self.rounds = []  # rounds[i][j] = time length of question j in round i
        self.recording = [[[] for i in range(self.questions_num)] for j in
                          range(self.rounds_num)]  # recording[i][j][k] = buzz time of round i, question j, buzz k
        self.answering_ids = []  # answering_ids[i][j] = answer of round i, question j

        questions_ptr = 0
        for i in range(self.rounds_num):
            round1 = []
            answering_ids1 = []
            for j in range(self.questions_num):
                round1.append(self.questions[questions_ptr][2])
                answering_ids1.append(self.questions[questions_ptr][1])
                questions_ptr += 1
            self.rounds.append(round1)
            self.answering_ids.append(answering_ids1)

    # returns the current game state
    # round #, question #, question time remaining, buzz time remaining, gap time remaining
    def gamestate(self):
        if not self.active_game:  # game is over
            return [self.active_game, 0, 0, 0, 0, 0, 0, self.points]
        if self.active_gap[0]:  # between questions
            # if gap time is over, move to question
            if self.get_gap_time() < 0:
                self.active_gap = [False, 0]
                self.active_question = [True, time.time()]

        if self.active_buzz[0]:  # in a buzz
            # if buzz time is over, keep going through question
            if self.get_buzz_time() < 0:
                if self.teams == 0:
                    self.points[self.active_buzz[3]] -= 5
                else:
                    for team in self.points:
                        if self.active_buzz[3] in team:
                            team[self.active_buzz[3]] -= 5
                self.active_question[1] = self.active_question[1] + self.buzz_time
                self.active_buzz = [False, 0, 0]
                self.buzzer = ''

        if self.active_question[0]:  # in a question
            # if question time is over, check round & question number- go to gap OR to next round OR end game
            if self.get_question_time() < 0:
                self.question_over()

        return [self.active_game, self.round, self.question, self.get_question_time(), self.get_buzz_time(),
                self.get_gap_time(), self.buzzer, self.points]

    # adjusts rounds when question is over
    def question_over(self):
        self.question += 1
        self.active_gap = [True, time.time()]
        self.active_question = [False, 0]
        if self.question > self.questions_num:
            self.question = 1
            self.round += 1
            if self.round > self.rounds_num:
                self.round = 0
                self.question = 0
                self.active_gap = [False, 0]
                self.active_game = False
                self.save_game()
                return

    # gets new question + tells HLS to get new question
    def get_new_question(self):
        return 1
        # question_idx = ((self.round-1) * self.questions_num) + self.question
        # hls_response = requests.post('http://127.0.0.1:3500/token',
        #                                 data={
        #                                     'handshake': HANDSHAKE,
        #                                     'qid': self.questions[question_idx][0]
        #                                 }
        #                              )
        # print(hls_response.text)
        # return {'token': hls_response['token'], 'rid': hls_response['rid']}

    # makes adjustments to timers when buzzing
    def buzz(self, username):
        if self.active_buzz[0] or not self.active_question[0]:
            return False
        else:
            self.buzzer = username
            self.active_buzz = [True, time.time(), self.get_question_time(), username]
            self.recording[self.round - 1][self.question - 1].append(['buzz', self.active_buzz[2], username])
            print('Buzzed at: ' + str(self.active_buzz[2]))
            return True

    # check answer while buzzed
    def answer(self, username, answer):
        # if game is over, return 0
        if not self.active_buzz[0]:
            return False
        else:
            correct = json.loads(requests.get('http://localhost:5000/answer',
                                              params={
                                                  'a': answer,
                                                  'qid': self.answering_ids[self.round - 1][self.question - 1],
                                              },
                                              headers={'Authorization': self.auth_token}).text)['correct']
            print('qb_id for current question: ' + str(self.answering_ids[self.round - 1][self.question - 1]))
            print(answer + " for Q:" + str(self.question) + "/R:" + str(self.round) + " was " + (
                "correct" if correct else "incorrect"))
            self.active_question[1] = time.time() - self.active_buzz[1] + self.active_question[
                1]  # readjust active question timer
            self.recording[self.round - 1][self.question - 1].append(
                ['answer', correct, self.get_buzz_time(), username])

            if correct:
                self.active_question[1] = time.time() - self.active_question[1] - self.rounds[self.round - 1][
                    self.question - 1]  # readjust active question timer
                if self.teams == 0:
                    self.points[username] += 10
                else:
                    for team in self.points:
                        if username in team:
                            team[username] += 10
            else:
                if self.teams == 0:
                    self.points[username] -= 5
                else:
                    for team in self.points:
                        if username in team:
                            team[username] -= 5
            print(self.points)
            self.active_buzz = [False, 0]
            self.buzzer = ""
            return True

    # get remaining question time
    def get_question_time(self):
        # if in the middle of a buzz, set the question time to the buzz time
        # if game is over, return 0
        if not self.active_game:
            return 0

        if self.active_question[0]:
            if self.active_buzz[0]:
                return self.active_buzz[2]
            else:
                return self.active_question[1] + self.rounds[self.round - 1][self.question - 1] - time.time()
        else:
            return self.rounds[self.round - 1][self.question - 1]

    # get remaining buzz time
    def get_buzz_time(self):
        if not self.active_game:
            return 0

        if self.active_buzz[0]:
            return self.active_buzz[1] + self.buzz_time - time.time()
        else:
            return self.buzz_time

    # get remaining gap time
    def get_gap_time(self):
        if not self.active_game:
            return 0

        if not self.active_gap[0]:
            return self.gap_time
        return self.active_gap[1] + self.gap_time - time.time()

    # save game's buzz times into text
    def save_game(self):
        f = open("recordings.txt", "w")
        for i in range(self.rounds_num):
            for j in range(self.questions_num):
                for k in range(len(self.recording[i][j])):
                    line = str(i + 1) + " " + str(j + 1) + " " + str(self.recording[i][j][k])
                    print(line)
                    f.write(line + "\n")
        f.close()

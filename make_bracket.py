import random

class Bracket:

    def __init__(self, teams, getProbs, team_to_str):
        self.teams = [(teams[i], 1.0) for i in range(len(teams))]
        self.getProbs = getProbs
        self.team_to_str = team_to_str

    def play_round(self):
        newTeams = []
        for i in range(len(self.teams)//2):
            prob1 = self.getProbs(self.teams[i*2][0], self.teams[i*2+1][0])
            prob2 = 1.0 - self.getProbs(self.teams[i*2+1][0],
                    self.teams[i*2][0])
            prob = (prob1 + prob2) / 2.0

            prob1 = prob * self.teams[i*2][1]
            prob2 = (1.0-prob) * self.teams[i*2+1][1]

            prob = prob1 / (prob1 + prob2)

            #rand = random.random() * random.random() * (1.0 if random.random() > 0.5 else -1.0) / 2 + 0.5
            if prob > 0.5:
            #if rand < prob:
                newTeams.append((self.teams[i*2][0], prob1))
            else:
                newTeams.append((self.teams[i*2+1][0], prob2))

        self.teams = newTeams

    def tournament(self):
        print('FIRST ROUND ', len(self.teams))
        print(self)
        while len(self.teams) > 1:
            self.play_round()
            print("PLAYING ROUND: ", len(self.teams))
            print(self)

        print("Winner: ", self.team_to_str(self.teams[0][0]),
                "%.3f" % (self.teams[0][1]))

    def __str__(self):
        s = ''

        for i in range(len(self.teams) // 2):
            team1 = self.team_to_str(self.teams[i*2][0])
            team2 = self.team_to_str(self.teams[i*2+1][0])

            prob1 = self.teams[i*2][1]
            prob2 = self.teams[i*2+1][1]

            cprob1 = self.getProbs(self.teams[i*2][0], self.teams[i*2+1][0])
            cprob2 = 1.0 - self.getProbs(self.teams[i*2+1][0],
                    self.teams[i*2][0])
            cprob = (cprob1 + cprob2) / 2.0

            s += '%20s %5.2f vs %-5.2f %-20s\t\t%.2f\n' % (team1,
                    prob1, prob2, team2, cprob)


        return s

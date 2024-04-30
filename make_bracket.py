import random

class TournamentSimulator:

    def __init__(self, participants, calculate_odds, participant_to_string):
        self.participants = [(participants[i], 1.0) for i in range(len(participants))]
        self.calculate_odds = calculate_odds
        self.participant_to_string = participant_to_string

    def play_match(self):
        next_round_participants = []
        for i in range(len(self.participants) // 2):
            odds_team1 = self.calculate_odds(self.participants[i*2][0], self.participants[i*2+1][0])
            odds_team2 = 1.0 - self.calculate_odds(self.participants[i*2+1][0], self.participants[i*2][0])
            average_odds = (odds_team1 + odds_team2) / 2.0

            adjusted_odds_team1 = average_odds * self.participants[i*2][1]
            adjusted_odds_team2 = (1.0 - average_odds) * self.participants[i*2+1][1]

            selection_probability = adjusted_odds_team1 / (adjusted_odds_team1 + adjusted_odds_team2)

            if selection_probability > 0.5:
                next_round_participants.append((self.participants[i*2][0], adjusted_odds_team1))
            else:
                next_round_participants.append((self.participants[i*2+1][0], adjusted_odds_team2))

        self.participants = next_round_participants

    def conduct_tournament(self):
        print('INITIAL ROUND: ', len(self.participants))
        print(self)
        while len(self.participants) > 1:
            self.play_match()
            print("NEXT ROUND: ", len(self.participants))
            print(self)

        print("Champion: ", self.participant_to_string(self.participants[0][0]), "%.3f" % (self.participants[0][1]))

    def __str__(self):
        result_str = ''
        for i in range(len(self.participants) // 2):
            name_team1 = self.participant_to_string(self.participants[i*2][0])
            name_team2 = self.participant_to_string(self.participants[i*2+1][0])

            odds_team1 = self.participants[i*2][1]
            odds_team2 = self.participants[i*2+1][1]

            current_odds_team1 = self.calculate_odds(self.participants[i*2][0], self.participants[i*2+1][0])
            current_odds_team2 = 1.0 - self.calculate_odds(self.participants[i*2+1][0], self.participants[i*2][0])
            match_odds = (current_odds_team1 + current_odds_team2) / 2.0

            result_str += '%20s %5.2f vs %-5.2f %-20s\t\t%.2f\n' % (name_team1, odds_team1, odds_team2, name_team2, match_odds)

        return result_str
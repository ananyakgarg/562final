import numpy as np
import p_rank
import pandas as pd


def get_parameter(param):
    def extract(data, index):
        return data[param][index]
    return extract

class DataBuilder:
    def __init__(self):
        self.year_to_team_to_league = {}
        self.team_id_to_name = {}
        self.league_stats_by_year = {}
        self.stats_by_year = {}

        self.load_team_names()
        self.load_team_leagues()
        self.initialize_league_stats()

    def load_team_names(self, file_name='MDataFiles_Stage3/MTeams.csv',
                        team_id='TeamID', team_name='TeamName'):
        data = pd.read_csv(file_name)
        for i in range(len(data[team_id])):
            if data[team_id][i] not in self.team_id_to_name:
                self.team_id_to_name[data[team_id][i]] = data[team_name][i]

    def load_team_leagues(self, file_name='MDataFiles_Stage3/MTeams.csv',
                          team_id='TeamID', year='Season', league='ConfAbbrev'):
        data = pd.read_csv('MDataFiles_Stage3/MTeamConferences.csv')
        for i in range(len(data[team_id])):
            if data[year][i] not in self.year_to_team_to_league:
                self.year_to_team_to_league[data[year][i]] = {}
            self.year_to_team_to_league[data[year][i]][data[team_id][i]] = data[league][i]

    def initialize_league_stats(self):
        for year in self.year_to_team_to_league:
            self.league_stats_by_year[year] = {}
            self.stats_by_year[year] = {}
            for team_id in self.year_to_team_to_league[year]:
                league_id = self.year_to_team_to_league[year][team_id]
                if league_id not in self.league_stats_by_year[year]:
                    self.league_stats_by_year[year][league_id] = {
                        'team_to_index': {},
                        'index_to_team': [],
                        'index': len(self.league_stats_by_year[year])
                    }
                index = len(self.league_stats_by_year[year][league_id]['index_to_team'])
                self.league_stats_by_year[year][league_id]['team_to_index'][team_id] = index
                self.league_stats_by_year[year][league_id]['index_to_team'].append(team_id)

    def prepare_data(self, data, setup_funcs, update_funcs, input_funcs, get_year=get_parameter("Season"),
                     get_winner_id=get_parameter("WTeamID"), get_winner_score=get_parameter("WScore"),
                     get_loser_id=get_parameter("LTeamID"), get_loser_score=get_parameter("LScore")):

        for func in setup_funcs:
            func(self)

        inputs, outputs = [], []
        for i in range(len(data)):
            if i > 1000 and i % 5000 == 0:
                print(f"{i} / {len(data)} {i / len(data):.2f}")

            season = get_year(data, i)
            winner_id = get_winner_id(data, i)
            winner_score = get_winner_score(data, i)
            loser_id = get_loser_id(data, i)
            loser_score = get_loser_score(data, i)

            winner_league_id = self.year_to_team_to_league[season][winner_id]
            loser_league_id = self.year_to_team_to_league[season][loser_id]

            winner_league_index = self.league_stats_by_year[season][winner_league_id]['index']
            loser_league_index = self.league_stats_by_year[season][loser_league_id]['index']

            winner_index = self.league_stats_by_year[season][winner_league_id]['team_to_index'][winner_id]
            loser_index = self.league_stats_by_year[season][loser_league_id]['team_to_index'][loser_id]

            for j in range(2):  # Create inputs for both outcomes
                new_input, new_output = [], [1 if j == 0 else 0]
                for func in input_funcs:
                    func(self, new_input, season,
                         winner_league_id, winner_league_index, winner_index, winner_score,
                         loser_league_id, loser_league_index, loser_index, loser_score)

                inputs.append(new_input)
                outputs.append(new_output)

                # Swap winner and loser for second outcome
                winner_league_id, winner_league_index, winner_index, winner_score, loser_league_id, loser_league_index, loser_index, loser_score = (
                loser_league_id, loser_league_index, loser_index, loser_score, winner_league_id, winner_league_index, winner_index, winner_score)

            # Update stats for future inputs
            for func in update_funcs:
                func(self, new_input, season,
                     winner_league_id, winner_league_index, winner_index, winner_score,
                     loser_league_id, loser_league_index, loser_index, loser_score)

        return inputs, outputs

def setup_page_rank(name):
    def initialize(self):
        for year in self.year_to_team_to_league:
            league_count = len(self.league_stats_by_year[year])
            self.stats_by_year[year][name] = [
                [0.0 for _ in range(league_count)] for _ in range(league_count)]
            for team_id in self.year_to_team_to_league[year]:
                league_id = self.year_to_team_to_league[year][team_id]
                team_count = len(
                    self.league_stats_by_year[year][league_id]['index_to_team'])
                self.league_stats_by_year[year][league_id][name] = [
                    [0.0 for _ in range(team_count)] for _ in range(team_count)]
    return initialize

def update_page_rank(name, wins_multiplier, goals_multiplier):
    def apply_update(self, new_input, season,
                     winner_league_id, winner_league_index, winner_index, winner_score,
                     loser_league_id, loser_league_index, loser_index, loser_score):

        if winner_league_id == loser_league_id:
            self.league_stats_by_year[season][winner_league_id][name][loser_index][winner_index] += wins_multiplier
            self.league_stats_by_year[season][winner_league_id][name][loser_index][winner_index] += winner_score * goals_multiplier
            self.league_stats_by_year[season][winner_league_id][name][winner_index][loser_index] += loser_score * goals_multiplier
        else:
            winner_adj_matrix = np.array(self.league_stats_by_year[season][winner_league_id][name])
            winner_ranks = p_rank.rank(winner_adj_matrix, 2)
            winner_rank = winner_ranks[winner_index][0]

            loser_adj_matrix = np.array(self.league_stats_by_year[season][loser_league_id][name])
            loser_ranks = p_rank.rank(loser_adj_matrix, 2)
            loser_rank = loser_ranks[loser_index][0]

            self.stats_by_year[season][name][loser_league_index][winner_league_index] += loser_rank * wins_multiplier
            self.stats_by_year[season][name][loser_league_index][winner_league_index] += loser_rank * winner_score * goals_multiplier
            self.stats_by_year[season][name][winner_league_index][loser_league_index] += winner_rank * loser_score * goals_multiplier

    return apply_update

verbal = False


def add_page_rank_to_inputs(name):
    def append_page_rank(self, new_input, season,
                         winner_league_id, winner_league_index, winner_index, winner_score,
                         loser_league_id, loser_league_index, loser_index, loser_score):
        # Winning team
        winner_adj_matrix = np.array(self.league_stats_by_year[season][winner_league_id][name])
        winner_ranks = p_rank.rank(winner_adj_matrix, 8)
        new_input.append(winner_ranks[winner_index][0])

        # Losing team
        loser_adj_matrix = np.array(self.league_stats_by_year[season][loser_league_id][name])
        loser_ranks = p_rank.rank(loser_adj_matrix, 8)
        new_input.append(loser_ranks[loser_index][0])

        # League
        league_adj_matrix = np.array(self.stats_by_year[season][name])
        league_ranks = p_rank.rank(league_adj_matrix, 2)
        new_input.append(league_ranks[winner_league_index][0])
        new_input.append(league_ranks[loser_league_index][0])

    return append_page_rank

def setup_win_percent(name):
    def initialize_win_percent(self):
        for year in self.year_to_team_to_league:
            self.stats_by_year[year][name] = {}
            if year not in self.league_stats_by_year:
                self.league_stats_by_year[year] = {}
            for team_id in self.year_to_team_to_league[year]:
                league_id = self.year_to_team_to_league[year][team_id]
                team_count = len(self.league_stats_by_year[year][league_id]['index_to_team'])
                self.league_stats_by_year[year][league_id][name] = [[] for _ in range(team_count)]
                self.stats_by_year[year][name][league_id] = []

    return initialize_win_percent

def update_win_percent(name, games_to_consider=0):
    def update(self, new_input, season,
               winner_league_id, winner_league_index, winner_index, winner_score,
               loser_league_id, loser_league_index, loser_index, loser_score):
        # Update winner's stats
        winner_stats = self.league_stats_by_year[season][winner_league_id][name][winner_index]
        winner_stats.append(1.0)  # Win recorded as 1.0
        self.league_stats_by_year[season][winner_league_id][name][winner_index] = winner_stats[-games_to_consider:]

        # Update loser's stats
        loser_stats = self.league_stats_by_year[season][loser_league_id][name][loser_index]
        loser_stats.append(0.0)  # Loss recorded as 0.0
        self.league_stats_by_year[season][loser_league_id][name][loser_index] = loser_stats[-games_to_consider:]

        # Update seasonal stats
        self.stats_by_year[season][name][winner_league_id].append(1.0)
        self.stats_by_year[season][name][loser_league_id].append(0.0)
        self.stats_by_year[season][name][winner_league_id] = self.stats_by_year[season][name][winner_league_id][-games_to_consider:]
        self.stats_by_year[season][name][loser_league_id] = self.stats_by_year[season][name][loser_league_id][-games_to_consider:]

    return update

def add_win_percent_to_inputs(name):
    def append_win_percent(self, new_input, season,
                           winner_league_id, winner_league_index, winner_index, winner_score,
                           loser_league_id, loser_league_index, loser_index, loser_score):

        # Calculate win percentage for the winner
        winner_wins = np.array(self.league_stats_by_year[season][winner_league_id][name][winner_index]).sum()
        winner_total = len(self.league_stats_by_year[season][winner_league_id][name][winner_index])
        winner_win_percent = winner_wins / winner_total if winner_total != 0 else 0

        # Calculate win percentage for the loser
        loser_wins = np.array(self.league_stats_by_year[season][loser_league_id][name][loser_index]).sum()
        loser_total = len(self.league_stats_by_year[season][loser_league_id][name][loser_index])
        loser_win_percent = loser_wins / loser_total if loser_total != 0 else 0

        new_input.extend([winner_win_percent, loser_win_percent])

        # Calculate seasonal win percentages
        season_winner_wins = np.array(self.stats_by_year[season][name][winner_league_id]).sum()
        season_winner_total = len(self.stats_by_year[season][name][winner_league_id])
        season_winner_win_percent = season_winner_wins / season_winner_total if season_winner_total != 0 else 0

        season_loser_wins = np.array(self.stats_by_year[season][name][loser_league_id]).sum()
        season_loser_total = len(self.stats_by_year[season][name][loser_league_id])
        season_loser_win_percent = season_loser_wins / season_loser_total if season_loser_total != 0 else 0

        new_input.extend([season_winner_win_percent, season_loser_win_percent])

    return append_win_percent

def add_inputs_and_outputs(model, dataset):
    inputs, outputs = model.prepare_data(
        dataset,
        [
            setup_page_rank('PageRankWins'),
            setup_page_rank('PageRankGoals'),
            setup_win_percent('Wins10'),
            setup_win_percent('Wins0'),
        ],
        [
            update_page_rank('PageRankWins', 1.0, 0.0),
            update_page_rank('PageRankGoals', 0.0, 1.0),
            update_win_percent('Wins10', 10),
            update_win_percent('Wins0', 0),
        ],
        [
            add_page_rank_to_inputs('PageRankWins'),
            add_page_rank_to_inputs('PageRankGoals'),
            add_win_percent_to_inputs('Wins10'),
            add_win_percent_to_inputs('Wins0'),
        ])

    return inputs, outputs

def get_data():
    model = DataBuilder()

    regular_season_data = pd.read_csv('MDataFiles_Stage3/MRegularSeasonCompactResults.csv')
    model.prepare_data(
        regular_season_data,
        [
            setup_page_rank('PageRankWins'),
            setup_page_rank('PageRankGoals'),
            setup_win_percent('Wins10'),
            setup_win_percent('Wins0'),
        ],
        [
            update_page_rank('PageRankWins', 1.0, 0.0),
            update_page_rank('PageRankGoals', 0.0, 1.0),
            update_win_percent('Wins10', 10),
            update_win_percent('Wins0', 0),
        ],
        []  # No input functions used here
    )

    global verbose
    verbose = True

    tournament_data = pd.read_csv('MDataFiles_Stage3/MNCAATourneyCompactResults.csv')
    inputs, outputs = model.prepare_data(
        tournament_data,
        [],
        [],
        [
            add_page_rank_to_inputs('PageRankWins'),
            add_page_rank_to_inputs('PageRankGoals'),
            add_win_percent_to_inputs('Wins10'),
            add_win_percent_to_inputs('Wins0'),
        ])

    training_inputs = np.array(inputs)
    training_outputs = np.array(outputs)
    testing_inputs = np.array(inputs)
    testing_outputs = np.array(outputs)

    return model, training_inputs, training_outputs, testing_inputs, testing_outputs

def get_inputs(model, season, team1, team2):
    data_dict = {
        'Season': [season], 'DayNum': [155], 'WTeamID': [team1],
        'WScore': [0], 'LTeamID': [team2], 'LScore': [0],
        'WLoc': ['N'], 'NumOT': [0]
    }
    match_data = pd.DataFrame(data=data_dict)

    inputs, _ = model.prepare_data(
        match_data, [], [], [
            add_page_rank_to_inputs('PageRankWins'),
            add_page_rank_to_inputs('PageRankGoals'),
            add_win_percent_to_inputs('Wins10'),
            add_win_percent_to_inputs('Wins0'),
        ])

    return np.array(inputs)



if __name__ == "__main__":
    m, training_inputs, training_outputs, testing_inputs, testing_outputs = getData()

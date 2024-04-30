import numpy as np
import p_rank
import pandas as pd


def getParameter(param):
    def f(data, index):
        return data[param][index]
    return f

class MakeData:
    def __init__(self):
        self.year_to_teamid_to_leagueid = {}
        self.teamid_to_teamname = {}
        self.year_to_league_stats = {}
        self.year_to_stats = {}

        self.readTeamIdToTeamName()
        self.readTeamIdToLeagueId()
        self.createYearToLeagueStats()

    def readTeamIdToTeamName(self, fileName='MDataFiles_Stage3/MTeams.csv',
                             teamId='TeamID', teamName='TeamName'):
        data = pd.read_csv('MDataFiles_Stage3/MTeams.csv')
        for i in range(len(data[teamId])):
            if data[teamId][i] not in self.teamid_to_teamname:
                self.teamid_to_teamname[data[teamId][i]] = data[teamName][i]

    def readTeamIdToLeagueId(self, fileName='MDataFiles_Stage3/MTeams.csv',
                             teamId='TeamID', year='Season', league='ConfAbbrev'):
        data = pd.read_csv('MDataFiles_Stage3/MTeamConferences.csv')
        for i in range(len(data[teamId])):
            if data[year][i] not in self.year_to_teamid_to_leagueid:
                self.year_to_teamid_to_leagueid[data[year][i]] = {}

            self.year_to_teamid_to_leagueid[
                data[year][i]][data[teamId][i]] = data[league][i]

    def createYearToLeagueStats(self):
        for year in self.year_to_teamid_to_leagueid:
            self.year_to_league_stats[year] = {}
            self.year_to_stats[year] = {}
            for teamId in self.year_to_teamid_to_leagueid[year]:
                leagueId = self.year_to_teamid_to_leagueid[year][teamId]

                if leagueId not in self.year_to_league_stats[year]:
                    self.year_to_league_stats[year][leagueId] = {
                        'indexToTeam': [],
                        'teamToIndex': {},
                        'index': len(self.year_to_league_stats[year])
                    }

                self.year_to_league_stats[year][leagueId]['teamToIndex'][teamId] = len(
                    self.year_to_league_stats[year][leagueId]['indexToTeam'])
                self.year_to_league_stats[year][leagueId]['indexToTeam'].append(teamId)

    def createInputsAndOutputs(self, data, setupFuncs, createDataFuncs,
                               collectInputFuncs, getYear=getParameter("Season"),
                               getWTeamId=getParameter("WTeamID"), getWScore=getParameter("WScore"),
                               getLTeamId=getParameter("LTeamID"), getLScore=getParameter("LScore")):

        for f in setupFuncs:
            f(self)

        inputs = []
        outputs = []
        for i in range(len(data)):

            if i > 1000 and i % 5000 == 0:
                print(i, '/', len(data), i / len(data))

            season = getYear(data, i)
            # if season < 2015:
            #    continue
            wId = getWTeamId(data, i)
            wScore = getWScore(data, i)
            lId = getLTeamId(data, i)
            lScore = getLScore(data, i)

            wLeagueId = self.year_to_teamid_to_leagueid[season][wId]
            lLeagueId = self.year_to_teamid_to_leagueid[season][lId]

            wLeagueIndex = self.year_to_league_stats[season][wLeagueId]['index']
            lLeagueIndex = self.year_to_league_stats[season][lLeagueId]['index']

            wIndex = self.year_to_league_stats[season][wLeagueId]['teamToIndex'][wId]
            lIndex = self.year_to_league_stats[season][lLeagueId]['teamToIndex'][lId]

            # Collect Data To Inputs
            for i in range(2):
                new_input = []
                new_output = [1 if i == 0 else 0]
                for f in collectInputFuncs:
                    f(self, new_input, season,
                      wLeagueId, wLeagueIndex, wIndex, wScore,
                      lLeagueId, lLeagueIndex, lIndex, lScore)

                inputs.append(new_input)
                outputs.append(new_output)

                rLeagueId, rLeagueIndex, rIndex, rScore = (lLeagueId, lLeagueIndex, lIndex, lScore)
                lLeagueId, lLeagueIndex, lIndex, lScore = (wLeagueId, wLeagueIndex, wIndex, wScore)
                wLeagueId, wLeagueIndex, wIndex, wScore = (rLeagueId, rLeagueIndex, rIndex, rScore)

            # Add the game to data for future inputs
            for f in createDataFuncs:
                f(self, new_input, season,
                  wLeagueId, wLeagueIndex, wIndex, wScore,
                  lLeagueId, lLeagueIndex, lIndex, lScore)

        return inputs, outputs


# MARK: Team Page Rank

def setUpPageRank(name):
    def f(self):
        for year in self.year_to_teamid_to_leagueid:
            teamCount = len(self.year_to_league_stats[year])
            self.year_to_stats[year][name] = [
                [0.0 for i in range(teamCount)] for j in range(teamCount)]
            for teamId in self.year_to_teamid_to_leagueid[year]:
                leagueId = self.year_to_teamid_to_leagueid[year][teamId]
                teamCount = len(
                    self.year_to_league_stats[year][leagueId]['indexToTeam'])
                self.year_to_league_stats[year][leagueId][name] = [
                    [0.0 for i in range(teamCount)] for j in range(teamCount)]

    return f


def updatePageRank(name, winsMultiplier, goalsMultiplier):
    def f(self, new_input, season,
          wLeagueId, wLeagueIndex, wIndex, wScore,
          lLeagueId, lLeagueIndex, lIndex, lScore):

        if wLeagueId == lLeagueId:
            self.year_to_league_stats[season][wLeagueId][name][lIndex][wIndex] += winsMultiplier
            self.year_to_league_stats[season][wLeagueId][name][lIndex][wIndex] += wScore * goalsMultiplier
            self.year_to_league_stats[season][wLeagueId][name][wIndex][lIndex] += lScore * goalsMultiplier
        else:

            wA = np.array(self.year_to_league_stats[season][wLeagueId][name])
            wR = p_rank.rank(wA, 2)
            wRank = wR[wIndex][0]

            lA = np.array(self.year_to_league_stats[season][lLeagueId][name])
            lR = p_rank.rank(lA, 2)
            lRank = lR[lIndex][0]

            self.year_to_stats[season][name][lLeagueIndex][wLeagueIndex] += lRank * winsMultiplier
            self.year_to_stats[season][name][lLeagueIndex][wLeagueIndex] += lRank * wScore * goalsMultiplier
            self.year_to_stats[season][name][wLeagueIndex][lLeagueIndex] += wRank * lScore * goalsMultiplier

    return f


verbal = False


def addPageRankToInputs(name):
    def f(self, new_input, season,
          wLeagueId, wLeagueIndex, wIndex, wScore,
          lLeagueId, lLeagueIndex, lIndex, lScore):
        # Winning team
        wA = np.array(self.year_to_league_stats[season][wLeagueId][name])
        wR = p_rank.rank(wA, 8)
        new_input.append(wR[wIndex][0])

        # Losing team
        lA = np.array(self.year_to_league_stats[season][lLeagueId][name])
        lR = p_rank.rank(lA, 8)
        new_input.append(lR[lIndex][0])

        # League
        A = np.array(self.year_to_stats[season][name])
        R = p_rank.rank(A, 2)
        new_input.append(R[wLeagueIndex][0])
        new_input.append(R[lLeagueIndex][0])


    return f


# MARK: Win Percent

def setUpWinPercent(name):
    def f(self):
        for year in self.year_to_teamid_to_leagueid:
            self.year_to_stats[year][name] = {}
            if year not in self.year_to_league_stats:
                self.year_to_league_stats[year] = {}
            for teamId in self.year_to_teamid_to_leagueid[year]:
                leagueId = self.year_to_teamid_to_leagueid[year][teamId]
                self.year_to_stats[year][name][leagueId] = []
                teamCount = len(self.year_to_league_stats[year][leagueId]['indexToTeam'])
                self.year_to_league_stats[year][leagueId][name] = [[] for j in range(teamCount)]

    return f


def updateWinPercent(name, gamesUsing=0):
    def f(self, new_input, season,
          wLeagueId, wLeagueIndex, wIndex, wScore,
          lLeagueId, lLeagueIndex, lIndex, lScore):
        self.year_to_league_stats[season][wLeagueId][name][wIndex].append(1.0)
        self.year_to_league_stats[season][wLeagueId][name][wIndex] = self.year_to_league_stats[season][wLeagueId][name][
                                                                         wIndex][-gamesUsing:]
        self.year_to_league_stats[season][lLeagueId][name][lIndex].append(0.0)
        self.year_to_league_stats[season][lLeagueId][name][lIndex] = self.year_to_league_stats[season][lLeagueId][name][
                                                                         lIndex][-gamesUsing:]

        # Season
        self.year_to_stats[season][name][wLeagueId].append(1.0)
        self.year_to_stats[season][name][lLeagueId].append(0.0)
        self.year_to_stats[season][name][wLeagueId] = self.year_to_stats[season][name][wLeagueId][-gamesUsing:]
        self.year_to_stats[season][name][lLeagueId] = self.year_to_stats[season][name][lLeagueId][-gamesUsing:]

    return f


def addWinPercentToInputs(name):
    def f(self, new_input, season,
          wLeagueId, wLeagueIndex, wIndex, wScore,
          lLeagueId, lLeagueIndex, lIndex, lScore):

        wWins = np.array(self.year_to_league_stats[season][wLeagueId][name][wIndex]).sum()
        wTotal = len(self.year_to_league_stats[season][wLeagueId][name][wIndex])
        if wTotal == 0:
            wTotal = 1

        lWins = np.array(self.year_to_league_stats[season][lLeagueId][name][lIndex]).sum()
        lTotal = len(self.year_to_league_stats[season][lLeagueId][name][lIndex])
        if lTotal == 0:
            lTotal = 1

        new_input.append(wWins / wTotal)
        new_input.append(lWins / lTotal)

        # Seasons

        wWins = np.array(self.year_to_stats[season][name][wLeagueId]).sum()
        wTotal = len(self.year_to_stats[season][name][wLeagueId])
        if wTotal == 0:
            wTotal = 1

        lWins = np.array(self.year_to_stats[season][name][lLeagueId]).sum()
        lTotal = len(self.year_to_stats[season][name][lLeagueId])
        if lTotal == 0:
            lTotal = 1

        new_input.append(wWins / wTotal)
        new_input.append(lWins / lTotal)

    return f


def addInInputsOutputs(m, data):
    inputs, outputs = m.createInputsAndOutputs(
        data,
        [
            setUpPageRank('PageRankWins'),
            setUpPageRank('PageRankGoals'),
            setUpWinPercent('Wins10'),
            setUpWinPercent('Wins0'),
        ],
        [
            updatePageRank('PageRankWins', 1.0, 0.0),
            updatePageRank('PageRankGoals', 0.0, 1.0),
            updateWinPercent('Wins10', 10),
            updateWinPercent('Wins0', 0),
        ],
        [
            addPageRankToInputs('PageRankWins'),
            addPageRankToInputs('PageRankGoals'),
            addWinPercentToInputs('Wins10'),
            addWinPercentToInputs('Wins0'),
        ])

    return inputs, outputs


def getData():
    m = MakeData()

    data = pd.read_csv('MDataFiles_Stage3/MRegularSeasonCompactResults.csv')
    m.createInputsAndOutputs(
        data,
        [
            setUpPageRank('PageRankWins'),
            setUpPageRank('PageRankGoals'),
            setUpWinPercent('Wins10'),
            setUpWinPercent('Wins0'),
        ],
        [
            updatePageRank('PageRankWins', 1.0, 0.0),
            updatePageRank('PageRankGoals', 0.0, 1.0),
            updateWinPercent('Wins10', 10),
            updateWinPercent('Wins0', 0),
        ],
        [  # No need to add data when we dont use it
            # addPageRankToInputs('PageRankWins'),
            # addPageRankToInputs('PageRankGoals'),
            # addWinPercentToInputs('Wins10'),
            # addWinPercentToInputs('Wins0'),
        ])


    global verbal
    verbal = True

    data = pd.read_csv('MDataFiles_Stage3/MNCAATourneyCompactResults.csv')
    inputs, outputs = m.createInputsAndOutputs(
        data,
        [],
        [],
        [
            addPageRankToInputs('PageRankWins'),
            addPageRankToInputs('PageRankGoals'),
            addWinPercentToInputs('Wins10'),
            addWinPercentToInputs('Wins0'),
        ])

    # training_inputs = np.array(inputs[:2117])
    # training_outputs = np.array(outputs[:2117])

    # testing_inputs = np.array(inputs[2117:])
    # testing_outputs = np.array(outputs[2117:])

    training_inputs = np.array(inputs)
    training_outputs = np.array(outputs)
    testing_inputs = np.array(inputs)
    testing_outputs = np.array(outputs)

    return m, training_inputs, training_outputs, testing_inputs, testing_outputs


def getInputs(m, season, team1, team2):
    d = {'Season': [season], 'DayNum': [155], 'WTeamID': [team1],
         'WScore': [0], 'LTeamID': [team2], 'LScore': [0],
         'WLoc': ['N'], 'NumOT': [0]}
    data = pd.DataFrame(data=d)

    inputs, _ = m.createInputsAndOutputs(
        data, [], [], [
            addPageRankToInputs('PageRankWins'),
            addPageRankToInputs('PageRankGoals'),
            addWinPercentToInputs('Wins10'),
            addWinPercentToInputs('Wins0'),
        ])

    return np.array(inputs)


if __name__ == "__main__":
    m, training_inputs, training_outputs, testing_inputs, testing_outputs = getData()

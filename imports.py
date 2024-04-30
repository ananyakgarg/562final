import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# To split the dataset into train and test datasets
from sklearn.model_selection import train_test_split

# To model the Gaussian Naive Bayes classifier
from sklearn.naive_bayes import GaussianNB
# Import confusion matrix functionality
from sklearn.metrics import confusion_matrix as sk_confusion_matrix
# To calculate the accuracy score of the model
from sklearn.metrics import accuracy_score
import re

#Import Massey
massey = pd.read_csv('data/MDataFiles_Stage3/MMasseyOrdinals_thruDay128.csv')
#Import Other files
cities = pd.read_csv('data/MDataFiles_Stage3/Cities.csv')
conferences = pd.read_csv('data/MDataFiles_Stage3/Conferences.csv')
conf_tourney = pd.read_csv('data/MDataFiles_Stage3/MConferenceTourneyGames.csv')
game_cities = pd.read_csv('data/MDataFiles_Stage3/MGameCities.csv')
tourney_results = pd.read_csv('data/MDataFiles_Stage3/MNCAATourneyCompactResults.csv')
detailed_tourney_results = pd.read_csv('data/MDataFiles_Stage3/MNCAATourneyDetailedResults.csv')
tourney_all = pd.read_csv('data/MDataFiles_Stage3/MNCAATourneySeedRoundSlots.csv')
tourney_seeds = pd.read_csv('data/MDataFiles_Stage3/MNCAATourneySeeds.csv')
tourney_slots = pd.read_csv('data/MDataFiles_Stage3/MNCAATourneySlots.csv')
reg_season = pd.read_csv('data/MDataFiles_Stage3/MRegularSeasonCompactResults.csv')
detailed_reg_season = pd.read_csv('data/MDataFiles_Stage3/MRegularSeasonDetailedResults.csv')
seasons = pd.read_csv('data/MDataFiles_Stage3/MSeasons.csv')
second_tourney = pd.read_csv('data/MDataFiles_Stage3/MSecondaryTourneyCompactResults.csv')
detailed_second_tourney = pd.read_csv('data/MDataFiles_Stage3/MSecondaryTourneyTeams.csv')
team_coaches = pd.read_csv('data/MDataFiles_Stage3/MTeamCoaches.csv')
team_conferences = pd.read_csv('data/MDataFiles_Stage3/MTeamConferences.csv')
teams = pd.read_csv('data/MDataFiles_Stage3/MTeams.csv')
teams_description = pd.read_csv('data/MTeams.csv')

rs = pd.read_csv("data/MDataFiles_Stage3/MRegularSeasonCompactResults.csv")
results_data = pd.read_csv("data/MDataFiles_Stage3/MRegularSeasonCompactResults.csv")
K = 45
HOME_ADVANTAGE = 10
rs = results_data
rs.head(3)
team_ids = set(rs.WTeamID).union(set(rs.LTeamID))
len(team_ids)
elo_dict = dict(zip(list(team_ids), [1500] * len(team_ids)))
rs['margin'] = rs.WScore - rs.LScore
def elo_pred(elo1, elo2):
    return(1. / (10. ** (-(elo1 - elo2) / 400.) + 1.))

def expected_margin(elo_diff):
    return((7.5 + 0.006 * elo_diff))

def elo_update(w_elo, l_elo, margin):
    elo_diff = w_elo - l_elo
    pred = elo_pred(w_elo, l_elo)
    mult = ((margin + 3.) ** 0.8) / expected_margin(elo_diff)
    update = K * mult * (1 - pred)
    return(pred, update)
assert np.all(rs.index.values == np.array(range(rs.shape[0]))), "Index is out of order."
preds = []
w_elo = []
l_elo = []

# Loop over all rows of the games dataframe
for row in rs.itertuples():

    # Get key data from current row
    w = row.WTeamID
    l = row.LTeamID
    margin = row.margin
    wloc = row.WLoc

    # Does either team get a home-court advantage?
    w_ad, l_ad, = 0., 0.
    if wloc == "H":
        w_ad += HOME_ADVANTAGE
    elif wloc == "A":
        l_ad += HOME_ADVANTAGE

    # Get elo updates as a result of the game
    pred, update = elo_update(elo_dict[w] + w_ad,
                              elo_dict[l] + l_ad,
                              margin)
    elo_dict[w] += update
    elo_dict[l] -= update

    # Save prediction and new Elos for each round
    preds.append(pred)
    w_elo.append(elo_dict[w])
    l_elo.append(elo_dict[l])
rs['w_elo'] = w_elo
rs['l_elo'] = l_elo
rs['elo_dif'] =rs['w_elo']-rs['l_elo']
print(rs[['elo_dif','margin']].corr().iloc[0,1])

plt.scatter(rs['elo_dif'],rs['margin'], alpha=.005)

rs_win = rs[['Season', 'DayNum', 'WTeamID', 'w_elo']]
rs_lose = rs[['Season', 'DayNum', 'LTeamID', 'l_elo']]

rs_win = rs_win.rename(columns={'WTeamID': 'TeamID', 'w_elo': 'elo'})
rs_lose = rs_lose.rename(columns={'LTeamID': 'TeamID', 'l_elo': 'elo'})
rs_all = rs_win.append(rs_lose)

final_elo = pd.DataFrame()
for team in rs_all['TeamID'].unique():
    for season in rs_all[rs_all['TeamID'] == team]['Season'].unique():
        append = rs_all[(rs_all['TeamID'] == team) & (rs_all['Season'] == season)].sort_values('DayNum',
                                                                                            ascending=False).iloc[0,:]
        final_elo = final_elo.append(append)

final_elo.head(2)

tourney_seeds = pd.read_csv('data/MDataFiles_Stage3/MNCAATourneySeeds.csv')

def removeletters(x):
    return re.sub('[^0-9]','', x)

tourney_seeds['Seed']=tourney_seeds['Seed'].apply(lambda x: removeletters(x)).apply(int)
df1=tourney_seeds.merge(tourney_results, left_on= ['TeamID','Season'], right_on=['WTeamID','Season'], how='left')

df1['TeamID1']=df1['WTeamID']
df1['TeamID2']=df1['LTeamID']
df1['Win']=np.where(df1['TeamID1']==df1['WTeamID'],1,0)
df1=df1.rename(columns={'Seed':'TeamID1Seed'})

df2=df1.merge(tourney_seeds, left_on= ['LTeamID','Season'], right_on=['TeamID','Season'], how='right')
df2=df2.rename(columns={'Seed':'TeamID2Seed','Win':'Team1Win'})
df2.drop(['TeamID_x','TeamID_y','NumOT','WLoc','LTeamID','WTeamID'], 1, inplace = True)

df2['Margin']=df2['WScore']-df2['LScore']
df2.drop(['WScore','LScore'], 1, inplace = True)

lose_df=df2[['TeamID2','TeamID1','TeamID2Seed','TeamID1Seed','Season']]
lose_df=lose_df.rename(columns={'TeamID2':'TeamID','TeamID1':'OppTeamID','TeamID2Seed':'Seed','TeamID1Seed':'OppSeed'})
lose_df['Win']=0

win_df=df2[['TeamID1','TeamID2','TeamID1Seed','TeamID2Seed','Season']]
win_df['Win']=1
win_df=win_df.rename(columns={'TeamID1':'TeamID','TeamID2':'OppTeamID','TeamID1Seed':'Seed','TeamID2Seed':'OppSeed'})

all_tourney_df=win_df.append(lose_df)

all_tourney_df=all_tourney_df.merge(final_elo, left_on=['OppTeamID','Season'], right_on=['TeamID','Season'],how='left')

all_tourney_df.drop(['TeamID_y'], 1, inplace = True)
all_tourney_df=all_tourney_df.rename(columns={'TeamID_x':'TeamID','elo':'Oppelo'})

all_tourney_df.head()

all_tourney_df=all_tourney_df.merge(final_elo, left_on=['TeamID','Season'], right_on=['TeamID','Season'],how='left')

all_tourney_df.drop(['DayNum_y','DayNum_x'], 1, inplace = True)

all_tourney_df=all_tourney_df[(~all_tourney_df['TeamID'].isnull()) & (~all_tourney_df['OppSeed'].isnull())]
all_tourney_df['elodif']=all_tourney_df['elo']-all_tourney_df['Oppelo']
all_tourney_df['seeddif']=all_tourney_df['Seed']-all_tourney_df['OppSeed']

features=all_tourney_df[['TeamID','OppSeed','Seed','Season','OppTeamID','elodif']]
target=all_tourney_df['Win']
features_train, features_test, target_train, target_test = train_test_split(features,
                                                target, test_size = 0.3)
target_test
clf = GaussianNB()
clf.fit(features_train, target_train)
target_pred = clf.predict(features_test)

accuracy_score(target_test, target_pred, normalize = True)

# Create and format a confusion matrix
def conf_matrix(y_test, y_predict):

    # Create the raw confusion matrix
    conf = sk_confusion_matrix(y_test, y_predict)

    # Format the confusion matrix nicely
    conf = pd.DataFrame(data=conf)
    conf.columns.name = 'Predicted label'
    conf.index.name = 'Actual label'

    # Return the confusion matrix
    return conf

conf_matrix(target_test, target_pred)

from sklearn import linear_model, datasets
clf = linear_model.LogisticRegression()
clf.fit(features_train, target_train)
target_pred = clf.predict(features_test)

accuracy_score(target_test, target_pred, normalize = True)

from sklearn import metrics
print(metrics.classification_report(target_test, target_pred))

df2022=tourney_seeds[tourney_seeds['Season']==2022]

teams2022=df2022['TeamID'].unique()

matchups=pd.DataFrame()
index=0
for team in teams2022:
    for team2 in teams2022:
        if team!=team2:
            index=index+1
            matchup=pd.DataFrame({'TeamID':team,'OppTeamID':team2},index=[index])
            matchups=matchups.append(matchup)

final_elo2022=final_elo[final_elo['Season']==2022][['TeamID','elo']]
matchups=matchups.merge(final_elo2022, left_on=['OppTeamID'],right_on=['TeamID'])
matchups.drop(labels=['TeamID_y'], inplace=True, axis=1)
matchups=matchups.rename(columns={'TeamID_x':'TeamID'})
matchups=matchups.rename(columns={'elo':'Oppelo'})
matchups=matchups.merge(final_elo2022, left_on=['TeamID'],right_on=['TeamID'])
matchups=matchups.merge(df2022, left_on=['OppTeamID'], right_on=['TeamID'])
matchups=matchups.rename(columns={'TeamID_x':'TeamID','Seed':'OppSeed'})
matchups.drop(['TeamID_y'], 1, inplace = True)
matchups.head(2)

matchups=matchups.merge(df2022, left_on=['TeamID'], right_on=['TeamID'])
matchups=matchups.rename(columns={'Season_x':'Season'})
matchups.drop(['Season_y'], 1, inplace = True)
matchups['elodif']=matchups['elo']-matchups['Oppelo']
matchups['seeddif']=matchups['Seed']-matchups['OppSeed']
features=matchups[['TeamID','OppSeed','Seed','Season','OppTeamID','elodif']]
probabilities=clf.predict_proba(features)
predictions=[]
for i in probabilities:
    predictions.append((i[1]))
matchups['prediction']=predictions
teams_description=teams_description.iloc[:,:2]
output=matchups.merge(teams_description, left_on=['OppTeamID'], right_on=['TeamID'])
output=output.rename(columns={'TeamName':'OppTeamName'})
output.drop(labels=['TeamID_y'], inplace=True, axis=1)
output=output.merge(teams_description, left_on=['TeamID_x'], right_on=['TeamID'])
output=output.rename(columns={'TeamID_x':'TeamID'})
output=output[['TeamName','OppTeamName','prediction','Seed','OppSeed','elo','Oppelo']]
output.to_csv('descriptive_output.csv')
matchups.merge(teams_description, left_on=['TeamID'], right_on=['TeamID']).groupby('TeamName').mean().\
    sort_values('prediction', ascending=False)

matchups_for_submission=matchups[matchups['TeamID']<matchups['OppTeamID']]
matchups_for_submission['ID'] = '2022_' + matchups_for_submission.TeamID.map(str) + "_" + \
                                matchups_for_submission.OppTeamID.map(str)
matchups_for_submission['pred']=matchups_for_submission['prediction']

sample = pd.read_csv('data/MDataFiles_Stage3/MSampleSubmissionStage2.csv')
del sample['Pred']
sample.shape

matchups_for_submission=matchups_for_submission[['ID','pred']]
matchups_for_submission.shape

matchups_for_submission['pred'].mean()

matchups_for_submission.to_csv('submission.csv', index=None)
from sklearn import svm
import numpy as np
import pandas as pd
import data as mdata
import make_bracket
import byear

import tensorflow as tf
print(tf.version.VERSION)

def initialize_svm_model(input_len, output_len):
    model = svm.SVC(kernel='rbf', probability=True)
    return model

def fit_model(model, data_manager, train_inputs, train_outputs, test_inputs, test_outputs):
    print('Shapes of Data:')
    print('Training:', train_inputs.shape, train_outputs.shape)
    print('Testing:', test_inputs.shape, test_outputs.shape)

    model.fit(train_inputs, train_outputs.ravel())
    print('Model training complete.')

    return data_manager, model

def generate_game_predictor(data_manager, model, year):
    def game_predictor(team1, team2):
        inputs = mdata.get_inputs(data_manager, year, team1, team2)
        probabilities = model.predict_proba(inputs)
        return probabilities[0][1] / sum(probabilities[0])
    return game_predictor

def convert_team_id_to_name(data_manager):
    def converter(team_id):
        return data_manager.team_id_to_name.get(team_id, f'{team_id}-unknown')
    return converter

def validate_predictions(input_data, output_data, comparison_func):
    correct_count, error_count = 0, 0
    for i in range(len(input_data)):
        home = comparison_func(input_data[i][0], input_data[i][2])
        away = comparison_func(input_data[i][1], input_data[i][3])
        if (home > away and output_data[i][0] == 1) or (home < away and output_data[i][0] == 0):
            correct_count += 1
        else:
            error_count += 1
    return correct_count, error_count

if __name__ == "__main__":
    data_manager, train_inputs, train_outputs, test_inputs, test_outputs = mdata.get_data()
    svm_model = initialize_svm_model(train_inputs.shape[1], train_outputs.shape[1])
    _, svm_model = fit_model(svm_model, data_manager, train_inputs, train_outputs, test_inputs, test_outputs)

    for year in [2016, 2018, 2019, 2021, 2022]:
        bracket_predictor = generate_game_predictor(data_manager, svm_model, year)
        team_namer = convert_team_id_to_name(data_manager)
        tournament_bracket = make_bracket.Bracket(byear.__dict__[f'the{year}Bracket'], bracket_predictor, team_namer)
        tournament_bracket.tournament()

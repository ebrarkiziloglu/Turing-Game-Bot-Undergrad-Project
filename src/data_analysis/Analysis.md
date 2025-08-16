# Data Analysis

## Preparation
- [x] Exclude the faulty games, where bot timoeut error occured. `FAULTY_GAMES`
- [x] Exclude the trial-rounds (first two) games. `TRIAL_GAMES`
- [x] Seperate the games for different experiment days. ith experiment day game_ids range from (1000 * i) to (1000 * (i+1)). 

## Discouse Analysis 

### Per Game
Save the following information for the non-faulty non-trial games: 
- [x] Players' usernames, colors, accusations, and scores.
- [x] The message frequency per user / bot
- [x] Overall message frequency
- [x] Average message length of each user / bot per game
- [x] Average message length of the game [of all messages in the game]
- [x] The game duration

### Per User
- [x] User's accusation flow from the 1st game to the 10th.
- [x] Is there a user who always found the bot?
- [x] Save users' scores
- [x] Make a leaderboard.
- [x] User's accusation time flow. 

## General Game Stats
- [x] Analyse the accusation results
- [x] Analyse the average message frequency
- [x] Analyse the average message length
- [x] Analyse the average game duration

## Experiment Flow
- [x] Analyse the accusation flows from the 3rd round to the 10th.
- [x] Analyse the average message frequency flow from the 3rd round to the 10th. 
- [x] Analyse the average message length flow from the 3rd round to the 10th. 
- [x] Analyse the average game duration flow from the 3rd round to the 10th. 
- [x] Plot a graph for each of these.
Also calculate the overall stats for all games:
- [x] Analyse the accusation results [percentages]
- [x] Analyse the average message frequency [in seconds]
- [x] Analyse the average message length [in char counts]
- [x] Analyse the average game duration [in seconds]


## Hocalarima notlar
Trial roundler da cikinca 72 game kaldi.




## Functions
- `parse_datetime`: 
    - Parse datetime string from SQLite.
    - Returns `datetime`.
- `get_experiment_day` : 
    - Determines which experiment day a game belongs to. 
    - Returns `int`.
- `normalize_accusation_pair` : 
    - Makes the accusation pairs unordered. 
    - Returns `tuple`.
- `calculate_scores` : 
    - Calculate scores based on both players' accusations and timing
    - Returns a tuple of 3 `int`
- `get_valid_game_ids` : 
    - Removes the faulty (bot timeout error) and trial-round games. 
    - Returns `JSON`.
- `identify_faulty_games` : 
    - Helped me find the games where bot timeout error occured.
    - Returns `JSON`.
- `calculate_message_stats` : 
    - Calculate message frequency and average length for a user in a specific game: avg_frequency & avg_length
    - Returns a tuple of 2 `int`
- `calculate_overall_message_stats` : 
    - Calculate overall message statistics for the game: avg_frequency & avg_length
    - Returns a tuple of 2 `int`
- `save_analysis_to_db`: 
    - Save game analysis results to the database
- `analyze_game` : 
    - Analyze a single game and return a very detailed statistics.
    - Returns a `dict`.
- `analyze_game_flow` : 
    - Analyze the game statistics flow throughout experiments.
    - 



| `player1_accused` field | `player2_accused` field | accusation time status                                | Scores   | Scores   | Scores  |
| ----------------------  | ----------------------- | ----------------------------------------------------- | -------- | -------- | ------- |
| Player 1                | Player 2                | accusation times                                      | Player 1 | Player 2 | Bot     |
| ----------------------- | ----------------------- | ----------------------------------------------------- | -------- | -------- | ------- |
| 0                       | 0                       |    does not matter                                    |    0     |    0     |   10    |
| 0                       | 1                       |    does not matter                                    |    0     |    10    |   6     |
| 0                       | 2                       |    does not matter                                    |    0     |    0     |   10    |
| 1                       | 0                       |    does not matter                                    |    10    |    0     |   6     |
| 2                       | 0                       |    does not matter                                    |    0     |    0     |   10    |
| 1                       | 1                       | `player1_accusation_time` < `player2_accusation_time` |    10    |    7     |   0     |
| 1                       | 1                       | `player1_accusation_time` > `player2_accusation_time` |    7     |    10    |   0     |
| 1                       | 2                       |    does not matter                                    |    10    |    0     |   8     |
| 2                       | 1                       |    does not matter                                    |    0     |    10    |   8     |
| 2                       | 2                       |    does not matter                                    |    0     |    0     |   10    |





## Games where the bot did not speak:
1103, Black         -> game ended fast
1203, Blue          -> game ended fast
1401, 1402, 1403,   -> bot error probably occured.
1501, 1502, 1503,   -> bot error probably occured.
1701, 
1802, 
1901, 1902,

2101, 2102, 2103, 
2401, 2402, 2403, 
2603, 
2703, 
2802, 2803, 
2901, 2902, 2903, 

3003, 
3502, 
3801, 3802, 

4401, 4402, 4403, 
4701, 4702, 
4801, 4802, 4803

exclude_games = [
    1401, 1402, 1403,   
    1501, 1502, 1503,   

    2101, 2102, 2103, 
    2401, 2402, 2403, 
    2802, 2803, 
    2901, 2902, 2903, 

    3801, 3802, 
    
    4401, 4402, 4403, 
    4701, 4702, 
    4801, 4802, 4803
    ]

### Games where either of the players did not speak: 
Games where player1 did not speak: [2603, 4803]
Games where player2 did not speak: [2903, 4501]

None of these are excluded from the data, as the games ended normally.





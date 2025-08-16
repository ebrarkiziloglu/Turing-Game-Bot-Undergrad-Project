DROP TABLE IF EXISTS game_analysis;
-- Table to store game analysis results
CREATE TABLE IF NOT EXISTS game_analysis (
    game_id INTEGER PRIMARY KEY NOT NULL,
    -- Player 1 stats
    player1_color TEXT NOT NULL,
    player1_username TEXT NOT NULL,
    player1_accusation INTEGER NOT NULL,
    player1_score INTEGER NOT NULL,
    -- Player 2 stats
    player2_color TEXT NOT NULL,
    player2_username TEXT NOT NULL,
    player2_accusation INTEGER NOT NULL,
    player2_score INTEGER NOT NULL,
    -- Bot stats
    bot_color TEXT NOT NULL,
    bot_score INTEGER NOT NULL,
    -- Game stats
    game_duration REAL NOT NULL,
    game_round INTEGER NOT NULL,
    -- Message frequencies
    message_freq_overall REAL NOT NULL,
    message_freq_player1 REAL NOT NULL,
    message_freq_player2 REAL NOT NULL,
    message_freq_bot REAL NOT NULL,
    -- Message lengths
    message_len_overall REAL NOT NULL,
    message_len_player1 REAL NOT NULL,
    message_len_player2 REAL NOT NULL,
    message_len_bot REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
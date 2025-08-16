CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY NOT NULL,
    player1_username TEXT NOT NULL,
    player1_color TEXT NOT NULL,
    player2_username TEXT NOT NULL,
    player2_color TEXT NOT NULL,
    bot_type TEXT DEFAULT 'openai',
    bot_color TEXT NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME DEFAULT NULL,
    duration INTEGER DEFAULT 300,       -- Duration in seconds, default is 5 minutes
    player1_accused INT DEFAULT 0,                -- Store details of accusation. 1 if they accuse the bot, 2 if they accuse the human, 0 if no accusation
    player1_accusation_time DATETIME DEFAULT NULL,
    player2_accused INT DEFAULT 0,
    player2_accusation_time DATETIME DEFAULT NULL,
    player1_score INTEGER DEFAULT 0,
    player2_score INTEGER DEFAULT 0,
    bot_score INTEGER DEFAULT 0,
    is_completed INTEGER DEFAULT 0, -- 0 = FALSE, 1 = TRUE
    FOREIGN KEY (player1_username) REFERENCES usernames(username),
    FOREIGN KEY (player2_username) REFERENCES usernames(username)
);
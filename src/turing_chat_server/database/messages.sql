CREATE TABLE IF NOT EXISTS messages (
    game_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    player_username TEXT NOT NULL,
    message_content TEXT NOT NULL CHECK(length(message_content) <= 255),
    sent_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, message_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);
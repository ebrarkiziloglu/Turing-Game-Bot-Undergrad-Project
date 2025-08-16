CREATE TABLE IF NOT EXISTS usersandgames (
    username TEXT,
    game_id INTEGER,
    player_order INTEGER, -- Renamed 'order' to 'player_order'
    FOREIGN KEY (username) REFERENCES usernames(username),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    PRIMARY KEY (username, player_order)
);
import sqlite3
import random
from datetime import datetime
import os

SQL_FOLDER = "./turing_chat_server/database"
DB_PATH = os.path.abspath("./turing_chat_server/database/turing.db")

def init_database():
    """
    Reads SQL files from the database folder and runs the CREATE TABLE statements
    to ensure tables exist in the database.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Iterate over all `.sql` files in the database folder
        for sql_file in os.listdir(SQL_FOLDER):
            if sql_file.endswith(".sql"):
                file_path = os.path.join(SQL_FOLDER, sql_file)
                with open(file_path, "r") as f:
                    sql_script = f.read()

                # Execute the SQL script
                cursor.executescript(sql_script)
                print(f"Executed {sql_file} successfully.")

        # Commit changes
        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
    finally:
        # Ensure the connection is closed
        if 'conn' in locals() and conn:
            conn.close()



COLORS = ['Orange', 'Purple', 'Blue', 'Red', 'Green', 'Black']

NAMES = [
    "Kid", "Ben", "Dan", "Eli",                                     # 4 users
    "Gus", "Hal", "Ivy", "Jan", "Kim", "Leo",                       # 6 users   - 1st
    "Max", "Sam", "Ace", "Ash", "Bea", "Dot",                       # 6 users   - 2nd
    "Eve", "Fay",  "Kit", "Moe", "Pip", "Rex",                      # 6 users   - 3rd
    "Zoe", "Abby", "Finn", "Jude", "Noel", "Tess",                  # 6 users   - 4th
    "Omar", "Cleo", "Lily", "Beau", "Nico", 
    "Tina", "Amir", "Drew", "Luca", "Mila", 
    "Quin", "Troy", "Rudy", "Zara", "Theo", 
    "Cora", "Elle", "Gray", "Kira", "Otis", "Wade", "Yuri"
]

INSERT_INTO_usernames = """
    INSERT INTO usernames (username, created_at)
    SELECT ?, ?
    WHERE NOT EXISTS (SELECT 1 FROM usernames WHERE username = ?);
"""

INSERT_INTO_usersandgames = """
    INSERT INTO usersandgames (username, game_id, player_order)
    VALUES (?, ?, ?)
"""

INSERT_INTO_games = """
    INSERT INTO games (game_id, player1_username, player1_color, player2_username, player2_color, bot_color)
    VALUES (?, ?, ?, ?, ?, ?)
"""


def insert_username(cursor, username: str):
    cursor.execute(INSERT_INTO_usernames, (username, datetime.now(), username))


def insert_users_and_games(cursor, username: str, games: list):
    player_order = 1
    for game_id in games:
        cursor.execute(INSERT_INTO_usersandgames, (username, game_id, player_order))
        player_order += 1


def insert_into_game(cursor, game_id: str, player1_username: str, player2_username: str): 
    player1_color, player2_color, bot_color = random.sample(COLORS, 3)
    cursor.execute(INSERT_INTO_games, (game_id, player1_username, player1_color, player2_username, player2_color, bot_color))


def insert_user_data(username: str, game_ids: list):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        insert_username(cursor, username)

        insert_users_and_games(cursor, username, game_ids)
        conn.commit()
        print("User data inserted successfully.")

    except sqlite3.Error as e:
        print("ERROR: An ERROR occurred:", e)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def insert_game_data(game_id: str, player1_username: str, player2_username: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        insert_username(cursor, player1_username)
        insert_username(cursor, player2_username)
        insert_into_game(cursor, game_id, player1_username, player2_username)

        conn.commit()
        print("Game data inserted successfully.")

    except sqlite3.Error as e:
        print("ERROR: An ERROR occurred:", e)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

###########################################################################

# The following users are added to the DB for testing purposes.
def trial_users():
    username_1 = 'aaa'
    username_2 = 'bbb'
    username_3 = 'ccc'
    username_4 = 'ddd'
    username_5 = 'eee'
    username_6 = 'fff'

    # Games IDs from 10 to 25.
    game_ids = [i for i in range(10, 26)]
    insert_user_data(username_1, game_ids)
    insert_user_data(username_2, game_ids)
    for game_id in game_ids:
        insert_game_data(game_id, username_1, username_2)
    
    game_ids = [i for i in range(30, 46)]
    insert_user_data(username_3, game_ids)
    insert_user_data(username_4, game_ids)
    for game_id in game_ids:
        insert_game_data(game_id, username_3, username_4)

    game_ids = [i for i in range(50, 66)]
    insert_user_data(username_5, game_ids)
    insert_user_data(username_6, game_ids)
    for game_id in game_ids:
        insert_game_data(game_id, username_5, username_6)


###########################################################################

NUM_OF_USERS = 6
NUM_OF_GAMES_PER_USER = 10
NUM_OF_USERS_PER_GAME = 2

game_IDs_for_six_people = [
    [1, 101, 201, 301, 401, 501, 601, 701, 801, 901],
    [2, 102, 202, 302, 402, 502, 601, 703, 801, 903],
    [3, 103, 203, 302, 403, 502, 602, 701, 802, 901],
    [3, 102, 203, 301, 402, 501, 603, 702, 803, 902],
    [2, 101, 202, 303, 401, 503, 602, 702, 802, 902],
    [1, 103, 201, 303, 403, 503, 603, 703, 803, 903] 
]

def six_people(game_IDs_for_six_people: list, names: list, base_game_id):
    """
    Insert data for six people and their games into the database.

    Parameters:
        game_IDs_for_six_people (list): Nested list of game IDs for each user.
        names (list): List of 6 participant names.
        base_game_id (int): Offset to add to each game ID.
    Returns:
        bool: True if the operation is successful, False otherwise.
    """

    if not all(isinstance(game_list, list) for game_list in game_IDs_for_six_people):
        print("ERROR: Invalid format for game_IDs_for_six_people. Expected a list of lists.")
        return False

    if len(names) != NUM_OF_USERS:
        print(f'ERROR: {len(names)} != {NUM_OF_USERS}')
        return False 

    users_and_games = {}
    games_and_usernames = {}

    try:
        for name_index, username in enumerate(names):
            if len(game_IDs_for_six_people[name_index]) != NUM_OF_GAMES_PER_USER:
                print(f'ERROR: {len(game_IDs_for_six_people[name_index])} != {NUM_OF_GAMES_PER_USER}')
                return False
            
            users_and_games[username] = []
            for game_id_offset in game_IDs_for_six_people[name_index]:
                game_id = game_id_offset + base_game_id
                users_and_games[username].append(game_id)
                
                if game_id in games_and_usernames:
                    games_and_usernames[game_id].append(username)
                else:
                    games_and_usernames[game_id] = [username]
        
        print(f'users_and_games: {users_and_games}')
        print(f'games_and_usernames: {games_and_usernames}')
        
        for user, games in users_and_games.items():
            insert_user_data(user, games)
        
        for game_id, users in games_and_usernames.items():
            if len(users) != NUM_OF_USERS_PER_GAME:
                print(f'ERROR: {len(users)} != {NUM_OF_USERS_PER_GAME}')
                return False
            insert_game_data(game_id, users[0], users[1])
        
        return True
    
    except sqlite3.Error as e:
        print(f"ERROR: Database error occurred: {e}")
        return False
    
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {e}")
        return False

def process_six_groups(names_for_exp, base_game_ids):
    for i, names in enumerate(names_for_exp):
        if not six_people(game_IDs_for_six_people, names, base_game_ids[i]):
            print(f'ERROR: Error adding the names and game_IDs for i: {i}')

###########################################################################

# TUE DEC 24 - 1st Six Participants
# NAMES_1 = [
#     "Gus", "Hal", "Ivy", "Jan", "Kim", "Leo", 
# ]

# # WED DEC 25 - 2nd Six Participants
# NAMES_2 = [
#     "Max", "Sam", "Ace", "Ash", "Bea", "Dot",   
# ]

# # THU DEC 26 - 3rd Six Participants
# NAMES_3 = [
#     "Eve", "Fay",  "Kit", "Moe", "Pip", "Rex", 
# ]

# # TUE DEC 31 - 4th Six Participants
NAMES_4 = [
    "Lily", "Abby", "Finn", "Jude", "Noel", "Tess", 
]

# NAMES_FOR_EXP = [NAMES_1, NAMES_2, NAMES_3, NAMES_4]
# BASE_GAME_ID_S = [1000, 2000, 3000, 4000]

if __name__ == "__main__":
    # init_database()
    trial_users()
    # process_six_groups([NAMES_1], [1000])
    # process_six_groups([NAMES_2], [2000])
    # process_six_groups([NAMES_3], [3000])
    process_six_groups([NAMES_4], [4000])
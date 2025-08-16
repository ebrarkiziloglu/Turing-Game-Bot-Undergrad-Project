# analysis.py
import sqlite3
import json, csv
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Any
from datetime import datetime
# import matplotlib.pyplot as plt
import numpy as np
import statistics
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
import nltk


DAY_1_NAMES = ["Gus", "Hal", "Ivy", "Jan", "Kim", "Leo"]
DAY_2_NAMES = ["Max", "Sam", "Ace", "Ash", "Bea", "Dot"]
DAY_3_NAMES = ["Eve", "Fay",  "Kit", "Moe", "Pip", "Rex"]
DAY_4_NAMES = ["Lily", "Abby", "Finn", "Jude", "Noel", "Tess"]
NAMES = DAY_1_NAMES + DAY_2_NAMES + DAY_3_NAMES + DAY_4_NAMES

TRIAL_GAMES_OFFSETS = [1, 2, 3, 101, 102, 103]
TRIAL_GAMES = [1000 * i + j for i in range(1, 5) for j in TRIAL_GAMES_OFFSETS]

FAULTY_GAMES = [
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

ACCUSATION_PATTERNS = {
    "(0, 0)": "No accusations",
    "(0, 1)": "One player accused bot",
    "(0, 2)": "One player accused human",
    "(1, 1)": "Both players accused bot",
    "(1, 2)": "One player accused bot, one player accused human",
    "(2, 2)": "Both players accused each other"
}

COLORS = {
    'Orange': '🟠', 
    'Purple': '🟣', 
    'Blue': '🔵', 
    'Red': '🔴', 
    'Green': '🟢', 
    'Black': '⚫'
}

def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string from SQLite."""
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None


def get_experiment_day(game_id: int) -> int:
    """
    Determines which experiment day a game belongs to.
    
    Args:
        game_id (int): The game ID
    
    Returns:
        int: Day number (1-4) or 0 if it's a debug game
    """
    if game_id < 1000:
        return 0
    day = (game_id // 1000)
    return day if 1 <= day <= 4 else 0


def normalize_accusation_pair(p1_acc: int, p2_acc: int) -> Tuple[int, int]:
    return tuple(sorted([p1_acc, p2_acc]))


def calculate_scores(p1_acc: int, p2_acc: int, p1_time: datetime, p2_time: datetime) -> Tuple[int, int, int]:
    """Calculate scores based on accusations and timing."""
    if p1_acc == 0 and p2_acc == 0:
        return 0, 0, 10
    elif p1_acc == 0 and p2_acc == 1:
        return 0, 10, 6
    elif p1_acc == 0 and p2_acc == 2:
        return 0, 0, 10
    elif p1_acc == 1 and p2_acc == 0:
        return 10, 0, 6
    elif p1_acc == 2 and p2_acc == 0:
        return 0, 0, 10
    elif p1_acc == 1 and p2_acc == 1:
        if p1_time < p2_time:
            return 10, 7, 0
        else:
            return 7, 10, 0
    elif p1_acc == 1 and p2_acc == 2:
        return 10, 0, 8
    elif p1_acc == 2 and p2_acc == 1:
        return 0, 10, 8
    elif p1_acc == 2 and p2_acc == 2:
        return 0, 0, 10
    return 0, 0, 0  # Default case


def get_valid_game_ids(db_path: str) -> Dict[str, any]:
    """Get non faulty non-trial game IDs"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all game IDs
    cursor.execute("SELECT game_id FROM games WHERE game_id >= 1000 AND game_id < 5000")
    all_game_ids = set(row[0] for row in cursor.fetchall())
    
    # Remove faulty and trial games
    faulty_games = set(FAULTY_GAMES + TRIAL_GAMES)
    valid_game_ids = list(all_game_ids - faulty_games)
    
    # Group by day
    valid_games_by_day = {str(day): [] for day in range(1, 5)}
    for game_id in valid_game_ids:
        day = get_experiment_day(game_id)
        if day > 0:
            valid_games_by_day[str(day)].append(game_id)
    
    conn.close()
    
    return {
        "total_valid_games": len(valid_game_ids),
        "valid_games_by_day": valid_games_by_day,
        "valid_games_summary": {
            str(day): len(valid_games_by_day[str(day)]) 
            for day in range(1, 5)
        }
    }


def identify_faulty_games(db_path: str) -> Dict[str, any]:
    """Modified to return JSON-friendly dictionary"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        queries = {
            "silent_bot": """
                WITH GameMessages AS (
                    SELECT g.game_id, g.bot_color, 
                           COUNT(CASE WHEN m.player_username = g.bot_color THEN 1 END) as bot_message_count
                    FROM games g
                    LEFT JOIN messages m ON g.game_id = m.game_id
                    WHERE g.game_id >= 1000 AND g.game_id < 5000
                    GROUP BY g.game_id, g.bot_color
                )
                SELECT game_id
                FROM GameMessages
                WHERE bot_message_count = 0;
            """,
            "silent_player1": """
                WITH GameMessages AS (
                    SELECT g.game_id, g.player1_color, 
                           COUNT(CASE WHEN m.player_username = g.player1_color THEN 1 END) as player1_message_count
                    FROM games g
                    LEFT JOIN messages m ON g.game_id = m.game_id
                    WHERE g.game_id >= 1000 AND g.game_id < 5000
                    GROUP BY g.game_id, g.player1_color
                )
                SELECT game_id
                FROM GameMessages
                WHERE player1_message_count = 0;
            """,
            "silent_player2": """
                WITH GameMessages AS (
                    SELECT g.game_id, g.player2_color, 
                           COUNT(CASE WHEN m.player_username = g.player2_color THEN 1 END) as player2_message_count
                    FROM games g
                    LEFT JOIN messages m ON g.game_id = m.game_id
                    WHERE g.game_id >= 1000 AND g.game_id < 5000
                    GROUP BY g.game_id, g.player2_color
                )
                SELECT game_id
                FROM GameMessages
                WHERE player2_message_count = 0;
            """
        }
        
        # Execute queries and store results
        results = {}
        for key, query in queries.items():
            cursor.execute(query)
            results[key] = [row[0] for row in cursor.fetchall()]
        
        # Get total games count
        cursor.execute("SELECT COUNT(*) FROM games WHERE game_id >= 1000 AND game_id < 5000")
        total_games = cursor.fetchone()[0]
        
        return {
            "total_games": total_games,
            "silent_games": {
                "bot": results["silent_bot"],
                "player1": results["silent_player1"],
                "player2": results["silent_player2"]
            },
            "counts": {
                "silent_bot": len(results["silent_bot"]),
                "silent_player1": len(results["silent_player1"]),
                "silent_player2": len(results["silent_player2"])
            }
        }
        
    finally:
        if conn:
            conn.close()


def calculate_message_stats(conn: sqlite3.Connection, game_id: int, username: str) -> Tuple[float, float]:
    """
    Calculate message frequency and average length for a user in a specific game.
    
    Args:
        conn: Database connection
        game_id: ID of the game
        username: Username or color of the player/bot
        
    Returns:
        Tuple of (average frequency in seconds, average message length)
    """
    cursor = conn.cursor()
    
    # Get messages for this user in this game
    cursor.execute("""
        SELECT message_content, sent_time
        FROM messages
        WHERE game_id = ? AND player_username = ?
        ORDER BY sent_time
    """, (game_id, username))
    
    messages = cursor.fetchall()
    
    if not messages:
        return 0, 0
    # Calculate average message length
    total_length = sum(len(msg[0]) for msg in messages)
    avg_length = total_length / len(messages)
    
    # Calculate average frequency
    if len(messages) > 1:
        time_diffs = []
        for i in range(1, len(messages)):
            time1 = parse_datetime(messages[i-1][1])
            time2 = parse_datetime(messages[i][1])
            if time1 and time2:
                diff = (time2 - time1).total_seconds()
                time_diffs.append(diff)
        avg_frequency = sum(time_diffs) / len(time_diffs) if time_diffs else 0
    else:
        avg_frequency = 0
    return avg_frequency, avg_length


def calculate_overall_message_stats(conn: sqlite3.Connection, game_id: int) -> Tuple[float, float]:
    """Calculate overall message statistics for the game."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT message_content, sent_time
        FROM messages
        WHERE game_id = ?
        ORDER BY sent_time
    """, (game_id,))
    
    messages = cursor.fetchall()
    
    if not messages:
        return 0, 0

    # Calculate average message length
    total_length = sum(len(msg[0]) for msg in messages)
    avg_length = total_length / len(messages)

    # Calculate overall average frequency
    if len(messages) > 1:
        time_diffs = []
        for i in range(1, len(messages)):
            time1 = parse_datetime(messages[i-1][1])
            time2 = parse_datetime(messages[i][1])
            if time1 and time2:
                diff = (time2 - time1).total_seconds()
                time_diffs.append(diff)
        
        avg_frequency = sum(time_diffs) / len(time_diffs) if time_diffs else 0
    else:
        avg_frequency = 0
    return avg_frequency, avg_length


def save_analysis_to_db(conn: sqlite3.Connection, game_id: int, analysis: Dict[str, Any]) -> None:
    """Save game analysis results to the database."""
    cursor = conn.cursor()
    
    # Insert or update the analysis results
    cursor.execute("""
    INSERT OR REPLACE INTO game_analysis (
        game_id,
        player1_color, player1_username, player1_accusation, player1_score,
        player2_color, player2_username, player2_accusation, player2_score,
        bot_color, bot_score,
        game_duration, game_round,
        message_freq_overall, message_freq_player1, message_freq_player2, message_freq_bot,
        message_len_overall, message_len_player1, message_len_player2, message_len_bot
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        game_id,
        analysis['statistics']['player_1']['color'],
        analysis['statistics']['player_1']['username'],
        analysis['statistics']['player_1']['accusation'],
        analysis['statistics']['player_1']['score'],
        analysis['statistics']['player_2']['color'],
        analysis['statistics']['player_2']['username'],
        analysis['statistics']['player_2']['accusation'],
        analysis['statistics']['player_2']['score'],
        analysis['statistics']['bot']['color'],
        analysis['statistics']['bot']['score'],
        analysis['statistics']['game_duration'],
        analysis['statistics']['game_round'],
        analysis['message_frequency']['overall'],
        analysis['message_frequency']['player_1'],
        analysis['message_frequency']['player_2'],
        analysis['message_frequency']['bot'],
        analysis['message_length_average']['overall'],
        analysis['message_length_average']['player_1'],
        analysis['message_length_average']['player_2'],
        analysis['message_length_average']['bot']
    ))
    
    conn.commit()


def analyze_game(db_path: str, game_id: int) -> Dict[str, Any]:
    """Analyze a single game and return detailed statistics."""
    
    # Check if game should be excluded
    if game_id in FAULTY_GAMES or game_id in TRIAL_GAMES:
        return None
        
    conn = sqlite3.Connection(db_path)
    cursor = conn.cursor()
    
    try:
        # Get game base info
        cursor.execute("""
            SELECT 
                player1_username, player1_color, player1_accused, player1_accusation_time,
                player2_username, player2_color, player2_accused, player2_accusation_time,
                bot_color, start_time, end_time,
                bot_type
            FROM games 
            WHERE game_id = ?
        """, (game_id,))
        
        game_row = cursor.fetchone()
        if not game_row:
            conn.close()
            return None
        
        # Parse game data
        (p1_username, p1_color, p1_accused, p1_acc_time,
        p2_username, p2_color, p2_accused, p2_acc_time,
        bot_color, start_time, end_time, bot_type) = game_row
        
        # Convert times to datetime objects
        start_time = parse_datetime(start_time)
        end_time = parse_datetime(end_time)
        p1_acc_time = parse_datetime(p1_acc_time)
        p2_acc_time = parse_datetime(p2_acc_time)
        
        # Calculate game duration
        end_times = [t for t in [end_time, p1_acc_time, p2_acc_time] if t]
        game_duration = (min(end_times) - start_time).total_seconds() if end_times and start_time else 0
        
        # Calculate scores
        p1_score, p2_score, bot_score = calculate_scores(
            p1_accused or 0,
            p2_accused or 0,
            p1_acc_time,
            p2_acc_time
        )
        
        # Calculate message statistics
        p1_freq, p1_len = calculate_message_stats(conn, game_id, p1_color)
        p2_freq, p2_len = calculate_message_stats(conn, game_id, p2_color)
        bot_freq, bot_len = calculate_message_stats(conn, game_id, bot_color)
        overall_freq, overall_len = calculate_overall_message_stats(conn, game_id)
        
        # Create analysis dictionary
        analysis = {
            'statistics': {
                'player_1': {
                    'color': p1_color,
                    'username': p1_username,
                    'accusation': p1_accused or 0,
                    'score': p1_score
                },
                'player_2': {
                    'color': p2_color,
                    'username': p2_username,
                    'accusation': p2_accused or 0,
                    'score': p2_score
                },
                'bot': {
                    'color': bot_color,
                    'score': bot_score
                },
                'game_duration': game_duration,
                'game_round': (game_id % 1000) // 100 + 1
            },
            'message_frequency': {
                'overall': overall_freq,
                'player_1': p1_freq,
                'player_2': p2_freq,
                'bot': bot_freq
            },
            'message_length_average': {
                'overall': overall_len,
                'player_1': p1_len,
                'player_2': p2_len,
                'bot': bot_len
            }
        }
        
        # Save analysis to database
        save_analysis_to_db(conn, game_id, analysis)
    finally:
        return analysis
        conn.close()


def analyze_game_flow(db_path):
    """Analyze the game statistics flow throughout experiments."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize data structures for rounds 3-10
    rounds_data = {
        'message_freq': defaultdict(float),
        'message_freq_players': defaultdict(float),
        'message_freq_bot': defaultdict(float),
        'message_len': defaultdict(float),
        'message_len_players': defaultdict(float),
        'message_len_bot': defaultdict(float),
        'game_duration': defaultdict(float),
        'game_count': defaultdict(int),
        'accusations': defaultdict(lambda: defaultdict(int))
    }
    
    # Analyze rounds 3-10
    for round_num in range(3, 11):
        cursor.execute('''
            SELECT 
                AVG(message_freq_overall) as avg_freq,     
                AVG(message_freq_player1) as avg_freq_player1,
                AVG(message_freq_player2) as avg_freq_player2,
                AVG(message_freq_bot) as avg_freq_bot,
                AVG(message_len_overall) as avg_len,
                AVG(message_len_player1) as avg_len_player1,
                AVG(message_len_player2) as avg_len_player2,
                AVG(message_len_bot) as avg_len_bot,
                AVG(game_duration) as avg_duration,
                COUNT(*) as game_count,
                SUM(CASE WHEN player1_accusation = 0 AND player2_accusation = 0 THEN 1 ELSE 0 END) as acc_0_0,
                SUM(CASE WHEN (player1_accusation = 0 AND player2_accusation = 1) OR (player1_accusation = 1 AND player2_accusation = 0) THEN 1 ELSE 0 END) as acc_0_1,
                SUM(CASE WHEN (player1_accusation = 0 AND player2_accusation = 2) OR (player1_accusation = 2 AND player2_accusation = 0) THEN 1 ELSE 0 END) as acc_0_2,
                SUM(CASE WHEN player1_accusation = 1 AND player2_accusation = 1 THEN 1 ELSE 0 END) as acc_1_1,
                SUM(CASE WHEN (player1_accusation = 1 AND player2_accusation = 2) OR (player1_accusation = 2 AND player2_accusation = 1) THEN 1 ELSE 0 END) as acc_1_2,
                SUM(CASE WHEN player1_accusation = 2 AND player2_accusation = 2 THEN 1 ELSE 0 END) as acc_2_2
            FROM game_analysis
            WHERE game_round = ?
        ''', (round_num,))
        
        result = cursor.fetchone()
        
        if result:
            rounds_data['message_freq'][round_num] = result[0] or 0
            rounds_data['message_freq_players'][round_num] = statistics.mean([result[1], result[2]]) or 0
            rounds_data['message_freq_bot'][round_num] = result[3] or 0

            rounds_data['message_len'][round_num] = result[4] or 0
            rounds_data['message_len_players'][round_num] = statistics.mean([result[5], result[6]]) or 0
            rounds_data['message_len_bot'][round_num] = result[7] or 0

            rounds_data['game_duration'][round_num] = result[8] or 0
            rounds_data['game_count'][round_num] = result[9] or 0
            acc_patterns = {
                "(0, 0)": result[10] or 0,
                "(0, 1)": result[11] or 0,
                "(0, 2)": result[12] or 0,
                "(1, 1)": result[13] or 0,
                "(1, 2)": result[14] or 0,
                "(2, 2)": result[15] or 0
            }
            rounds_data['accusations'][round_num] = acc_patterns

    # Calculate overall statistics
    cursor.execute('''
        SELECT 
            AVG(message_freq_overall) as avg_freq,
            AVG(message_freq_player1) as avg_freq_player1,
            AVG(message_freq_player2) as avg_freq_player2,
            AVG(message_freq_bot) as avg_freq_bot,
            AVG(message_len_overall) as avg_len,
            AVG(message_len_player1) as avg_len_player1,
            AVG(message_len_player2) as avg_len_player2,
            AVG(message_len_bot) as avg_len_bot,
            AVG(game_duration) as avg_duration,
            COUNT(*) as total_games,
            SUM(CASE WHEN player1_accusation = 0 AND player2_accusation = 0 THEN 1 ELSE 0 END) as acc_0_0,
            SUM(CASE WHEN (player1_accusation = 0 AND player2_accusation = 1) OR (player1_accusation = 1 AND player2_accusation = 0) THEN 1 ELSE 0 END) as acc_0_1,
            SUM(CASE WHEN (player1_accusation = 0 AND player2_accusation = 2) OR (player1_accusation = 2 AND player2_accusation = 0) THEN 1 ELSE 0 END) as acc_0_2,
            SUM(CASE WHEN player1_accusation = 1 AND player2_accusation = 1 THEN 1 ELSE 0 END) as acc_1_1,
            SUM(CASE WHEN (player1_accusation = 1 AND player2_accusation = 2) OR (player1_accusation = 2 AND player2_accusation = 1) THEN 1 ELSE 0 END) as acc_1_2,
            SUM(CASE WHEN player1_accusation = 2 AND player2_accusation = 2 THEN 1 ELSE 0 END) as acc_2_2
        FROM game_analysis
    ''')
    
    overall_result = cursor.fetchone()
    total_games = overall_result[9]
    
    overall_stats = {
        'avg_message_freq': overall_result[0] or 0,
        'avg_message_freq_players': statistics.mean([overall_result[1], overall_result[2]]) or 0,
        'avg_message_freq_bot': overall_result[3] or 0,
        'avg_message_len': overall_result[4] or 0,
        'avg_message_len_players': statistics.mean([overall_result[5], overall_result[6]]) or 0,
        'avg_message_len_bot': overall_result[7] or 0,
        'avg_game_duration': overall_result[8] or 0,
        'game_count': total_games,
        'accusations': {
            'No accusations': (overall_result[10] / total_games) * 100 if total_games > 0 else 0,
            'One player accused bot': (overall_result[11] / total_games) * 100 if total_games > 0 else 0,
            'One player accused human': (overall_result[12] / total_games) * 100 if total_games > 0 else 0,
            'Both players accused bot': (overall_result[13] / total_games) * 100 if total_games > 0 else 0,
            'One accused bot, one human': (overall_result[14] / total_games) * 100 if total_games > 0 else 0,
            'Both accused each other': (overall_result[15] / total_games) * 100 if total_games > 0 else 0
        }
    }
    
    conn.close()
    return rounds_data, overall_stats

def analyze_user_stats(db_path):
    """
    Analyze user statistics including scores and accusation patterns.
    
    Args:
        db_path (str): Path to the SQLite database
        
    Returns:
        tuple: (user_stats, bot_total_score)
            - user_stats: Dictionary with user statistics
            - bot_total_score: Total score accumulated by the bot
    """
    # Initialize user statistics dictionary
    user_stats = {
        username: {
            'num_of_games': 0,
            'score': 0,
            'scores': { i : 0 for i in range(3, 11)},
            'accusations': { i : "" for i in range(3, 11)},
            'accusation_times': { i : 0 for i in range(3, 11)}
        } for username in NAMES
    }
    
    bot_total_score = 0
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query game analysis data
    cursor.execute('''
        SELECT 
            game_id,
            player1_username,
            player1_accusation,
            player1_score,
            player2_username,
            player2_accusation,
            player2_score,
            bot_score,
            game_round
        FROM game_analysis
        WHERE game_round BETWEEN 3 AND 10
    ''')
    
    # Process each game
    for row in cursor.fetchall():
        (game_id, p1_username, p1_accusation, p1_score,
         p2_username, p2_accusation, p2_score,
         bot_score, game_round) = row
        
        # Update player 1 statistics
        if p1_username in user_stats:
            user_stats[p1_username]['num_of_games'] += 1
            user_stats[p1_username]['score'] += p1_score or 0
            user_stats[p1_username]['scores'][game_round] = p1_score or 0
            user_stats[p1_username]['accusations'][game_round] = str(p1_accusation if p1_accusation is not None else "")
        
        # Update player 2 statistics
        if p2_username in user_stats:
            user_stats[p2_username]['num_of_games'] += 1
            user_stats[p2_username]['score'] += p2_score or 0
            user_stats[p2_username]['scores'][game_round] = p2_score or 0
            user_stats[p2_username]['accusations'][game_round] = str(p2_accusation if p2_accusation is not None else "")
        
        # Update bot score
        bot_total_score += bot_score or 0

    faulty_games = set(FAULTY_GAMES + TRIAL_GAMES)

# Query game analysis data
    cursor.execute('''
        SELECT 
            game_id,
            start_time,
            player1_username,
            player1_accusation_time,
            player2_username,
            player2_accusation_time
        FROM games
        WHERE game_id BETWEEN 1000 AND 5000
    ''')
    
    # Process each game
    for row in cursor.fetchall():
        (game_id, start_time,
        p1_username, p1_acc_time, 
        p2_username, p2_acc_time) = row
        game_round = (game_id % 1000) // 100 + 1

        if game_id not in faulty_games:
            game_round = (game_id % 1000) // 100 + 1
            
            # Parse times only if they exist
            start_dt = parse_datetime(start_time) if start_time else None
            p1_acc_dt = parse_datetime(p1_acc_time) if p1_acc_time else None
            p2_acc_dt = parse_datetime(p2_acc_time) if p2_acc_time else None
            
            # Calculate durations only if both times exist
            p1_acc_duration = -1
            p2_acc_duration = -1

            if start_dt and p1_acc_dt:
                p1_acc_duration = (p1_acc_dt - start_dt).total_seconds()
            
            if start_dt and p2_acc_dt:
                p2_acc_duration = (p2_acc_dt - start_dt).total_seconds()

            # Update player 1 statistics
            if p1_username in user_stats:
                user_stats[p1_username]['accusation_times'][game_round] = p1_acc_duration
            
            # Update player 2 statistics
            if p2_username in user_stats:
                user_stats[p2_username]['accusation_times'][game_round] = p2_acc_duration
        
    conn.close()
    
    return user_stats, bot_total_score


def save_user_stats(user_stats, bot_total_score, output_filename=None):
    """
    Save user statistics to a single CSV file with multiple tables.
    
    Args:
        user_stats (dict): Dictionary containing user statistics
        bot_total_score (float): Total score accumulated by the bot
        output_filename (str, optional): Output file name. If None, generates with timestamp
    """
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'user_statistics_{timestamp}.csv'
    
    with open(output_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Table 1: User Statistics Summary
        writer.writerow(['USER STATISTICS SUMMARY'])
        writer.writerow(['Username', 'Games Played', 'Total Score', 'Average Score'])
        for username, stats in sorted(user_stats.items()):
            avg_score = stats['score'] / stats['num_of_games'] if stats['num_of_games'] > 0 else 0
            writer.writerow([
                username,
                stats['num_of_games'],
                stats['score'],
                f"{avg_score:.2f}"
            ])
        
        # Blank rows between tables
        writer.writerow([])
        writer.writerow([])
        
        # Table 2: Score Flow
        writer.writerow(['SCORE FLOW'])
        # Header row
        header = ['Username'] + [f'{i}' for i in range(3, 11)]
        writer.writerow(header)
        # Data rows
        for username, stats in sorted(user_stats.items()):
            scores = [stats['scores'][i] for i in range(3, 11)]
            writer.writerow([username] + scores)
        
        # Blank rows between tables
        writer.writerow([])
        writer.writerow([])
        
        # Table 3: Bot Score
        writer.writerow(['BOT STATISTICS'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Bot Score', bot_total_score])
        
        # Blank rows between tables
        writer.writerow([])
        writer.writerow([])
        
        # Table 4: Accusation Patterns
        writer.writerow(['ACCUSATION PATTERNS'])
        # Header row
        header = ['Username'] + [f'{i}' for i in range(3, 11)]
        writer.writerow(header)
        # Data rows
        for username, stats in sorted(user_stats.items()):
            accusations = [stats['accusations'][i] for i in range(3, 11)]
            writer.writerow([username] + accusations)

        # Blank rows between tables
        writer.writerow([])
        writer.writerow([])

        # Table 5: Accusation Times
        writer.writerow(['ACCUSATION TIMES'])
        # Header row
        header = ['Username'] + [f'{i}' for i in range(3, 11)]
        writer.writerow(header)
        # Data rows
        for username, stats in sorted(user_stats.items()):
            accusation_times = [stats['accusation_times'][i] for i in range(3, 11)]
            writer.writerow([username] + accusation_times)
    
    print(f"Statistics have been saved to: {output_filename}")

def get_user_games(cursor: sqlite3.Cursor, username: str) -> List[int]:
    """Get all game IDs for a specific user."""
    cursor.execute("""
        SELECT game_id 
        FROM usersandgames 
        WHERE username = ?
    """, (username,))
    return [row[0] for row in cursor.fetchall()]

def get_game_info(cursor: sqlite3.Cursor, game_id: int, username: str) -> Tuple[str, str, str]:
    """Get game colors info and determine which color belongs to the user."""
    cursor.execute("""
        SELECT 
            player1_username, player1_color,
            player2_username, player2_color,
            bot_color,
            player1_accused, player2_accused 
        FROM games 
        WHERE game_id = ?
    """, (game_id,))
    
    row = cursor.fetchone()
    if not row:
        return None, None, None
        
    p1_username, p1_color, p2_username, p2_color, bot_color, p1_accused, p2_accused = row
    p1_accusation, p2_accusation = '⭕ No', '⭕ No'
    if p1_accused == 1:
        p1_accusation = '✅ Correct'
    elif p1_accused == 2:
        p1_accusation = '❌ Incorrect'
    if p2_accused == 1:
        p2_accusation = '✅ Correct'
    elif p2_accused == 2:
        p2_accusation = '❌ Incorrect'
    p1_accusation += ' accusation'
    p2_accusation += ' accusation'

    if p1_username == username:
        return p1_color, p2_color, bot_color, p1_accusation, p2_accusation
    else:
        return p2_color, p1_color, bot_color, p2_accusation, p1_accusation

def get_game_messages(cursor: sqlite3.Cursor, game_id: int) -> List[Tuple[str, str]]:
    """Get all messages for a game in order."""
    cursor.execute("""
        SELECT player_username, message_content
        FROM messages
        WHERE game_id = ?
        ORDER BY message_id
    """, (game_id,))
    return cursor.fetchall()

def generate_user_chat_histories(db_path: str, output_dir: str = "turing_chat_server/data_analysis/user_chats"):
    """Generate markdown files containing chat histories for all users."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for name in NAMES:
        # Get all games for this user
        games = get_user_games(cursor, name)
        if not games:
            continue
            
        # Determine experiment day from first game
        day = games[0] // 1000
        
        # Create/open markdown file for this user
        # print(f"File created: Day_{day}_{name}.md")
        filename = os.path.join(output_dir, f"Day_{day}_{name}.md")
        with open(filename, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# Hello user {name}.\n\nThis file contains the chat histories of the games you participated in during our Turing Game Experiments.\n\n")
            
            # Process each game
            for game_count, game_id in enumerate(games, 1):
                # Get game colors
                own_color, opponents_color, bot_color, own_accusation, opponents_accusation = get_game_info(cursor, game_id, name)
                if not own_color:  # Skip if game info not found
                    continue
                
                # Write game header
                f.write(f"<details>\n<summary>Game {game_count}: (ID: {game_id})</summary>\n\n")

                f.write(f"| User | Color |\n| ---- | ----- |\n| You  | **{COLORS[own_color]} {own_color}** |\n")
                f.write(f"| Other human  | **{COLORS[opponents_color]} {opponents_color}** |\n")
                f.write(f"| Bot  | **{COLORS[bot_color]} {bot_color}** |\n")
                
                f.write("### The Chat:\n\n")
                # Get and write messages
                messages = get_game_messages(cursor, game_id)
                for username, content in messages:
                    f.write(f"({COLORS[username]}): **{content.strip()}**\n\n")
                
                f.write("### The Accusations:\n\n")

                f.write(f"| User | Accusation |\n| ---- | ----- |\n| You  | **{own_accusation}** |\n")
                f.write(f"| Other human  | **{opponents_accusation}** |\n")
                # Add separator between games
                f.write("</details>\n\n\n")
    
    conn.close()
    print(f"Chat histories have been generated in the '{output_dir}' directory.")


def tokenize_message(message: str) -> List[str]:
    """Convert message to tokens (words)."""
    # Convert to lowercase and split into words
    message = message.lower().strip()
    # Split on whitespace and remove empty tokens
    tokens = [token.strip() for token in message.split() if token.strip()]
    return tokens

def get_user_messages(cursor: sqlite3.Cursor, username: str) -> List[str]:
    """Get all messages written by a specific user."""
    cursor.execute("""
        SELECT game_id 
        FROM usersandgames 
        WHERE username = ?
    """, (username,))
    game_ids = [row[0] for row in cursor.fetchall()]
    
    user_messages = []
    for game_id in game_ids:
        user_color, _, _, _, _ = get_game_info(cursor, game_id, username)
        if user_color:
            cursor.execute("""
                SELECT message_content
                FROM messages
                WHERE game_id = ? AND player_username = ?
                ORDER BY message_id
            """, (game_id, user_color))
            messages = cursor.fetchall()
            user_messages.extend([msg[0] for msg in messages])
    
    return user_messages

def get_bot_messages(cursor: sqlite3.Cursor) -> List[str]:
    """Get all messages written by bots."""
    cursor.execute("""
        SELECT m.message_content
        FROM messages m
        JOIN games g ON m.game_id = g.game_id
        WHERE g.game_id BETWEEN 1000 AND 5000
        AND m.player_username = g.bot_color
        ORDER BY m.game_id, m.message_id
    """)
    return [msg[0] for msg in cursor.fetchall()]


def analyze_vocabulary(messages: List[str]) -> Dict[str, int]:
    """Analyze vocabulary frequency in messages."""
    token_freq = defaultdict(int)
    
    for message in messages:
        tokens = tokenize_message(message)
        for token in tokens:
            token_freq[token] += 1
            
    return dict(token_freq)

def save_messages_to_file(messages: List[str], filename: str):
    """Save messages to a text file."""
    with open(filename, 'w', encoding='utf-8') as f:
        for message in messages:
            f.write(message.strip() + '\n')


def analyze_all_vocabularies(db_path: str) -> Dict[str, Dict[str, int]]:
    """Analyze vocabularies for all users and bots."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Dictionary to store vocabulary analysis for each user
    vocab_analysis = {}
    
    # Process human users
    all_user_messages = []
    for username in NAMES:
        user_messages = get_user_messages(cursor, username)
        vocab_analysis[username] = analyze_vocabulary(user_messages)
        all_user_messages.extend(user_messages)
    
    # Save all user messages to file
    save_messages_to_file(all_user_messages, 'users_messages.txt')
    
    # Process bot messages
    bot_messages = get_bot_messages(cursor)
    vocab_analysis['bot'] = analyze_vocabulary(bot_messages)
    save_messages_to_file(bot_messages, 'bots_messages.txt')
    
    # Print some statistics
    print("\nVocabulary Analysis Summary:")
    for user, vocab in vocab_analysis.items():
        unique_words = len(vocab)
        total_words = sum(vocab.values())
        print(f"\n{user}:")
        print(f"Unique words: {unique_words}")
        print(f"Total words: {total_words}")
        print(f"Average word frequency: {total_words/unique_words:.2f}")
        
        # Print top 10 most frequent words
        top_words = sorted(vocab.items(), key=lambda x: x[1], reverse=True)[:10]
        print("Top 10 most frequent words:")
        for word, freq in top_words:
            print(f"  {word}: {freq}")
    
    conn.close()
    return vocab_analysis

def save_vocabulary_analysis(db_path: str):
    # Download required NLTK data
    nltk.download('stopwords')
    STOP_WORDS = set(stopwords.words('english'))
    
    # Run analysis
    vocab_analysis = analyze_all_vocabularies(db_path)
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Merge all user vocabularies (excluding bot)
    all_users_vocab = Counter()
    for username, vocab in vocab_analysis.items():
        if username != "bot":  # Exclude bot from all_users
            all_users_vocab.update(vocab)
    
    # Add all_users to vocab_analysis
    vocab_analysis["all_users"] = dict(all_users_vocab)
    
    def get_top_words_no_stops(vocab_dict, n=20):
        """Get top N words excluding stop words"""
        return [
            (word, count) for word, count in 
            sorted(vocab_dict.items(), key=lambda x: x[1], reverse=True)
            if word.lower() not in STOP_WORDS
        ][:n]
    
    def generate_wordcloud(vocab_dict, title):
        """Generate and save wordcloud for given vocabulary"""
        # Filter out stop words
        filtered_vocab = {
            word: count for word, count in vocab_dict.items() 
            if word.lower() not in STOP_WORDS
        }
        
        if not filtered_vocab:  # Skip if no words remain after filtering
            return
        
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            min_font_size=10
        ).generate_from_frequencies(filtered_vocab)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(title)
        plt.savefig(f'wordcloud_{title.lower().replace(" ", "_")}.png')
        plt.close()
    
    # Create structured output with new features
    analysis_output = {
        "metadata": {
            "timestamp": timestamp,
            "total_users_analyzed": len(NAMES),
            "users": NAMES
        },
        "vocabulary_analysis_summary": {
            username: {
                "unique_words": len(vocab),
                "total_words": sum(vocab.values()),
                "avg_word_frequency": sum(vocab.values()) / len(vocab) if vocab else 0,
                "top_10_words": sorted(vocab.items(), key=lambda x: x[1], reverse=True)[:10],
                "top_20_no_stopwords": get_top_words_no_stops(vocab)
            }
            for username, vocab in vocab_analysis.items()
        },
        "vocabulary_analysis": vocab_analysis
    }
    
    # Save to JSON file
    json_filename = f"vocabulary_analysis.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_output, f, indent=2)
    
    # Save summary statistics to CSV
    csv_filename = f"vocabulary_statistics.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['username', 'unique_words', 'total_words', 'avg_word_frequency'])
        
        # Write data for each user and bot
        for username, vocab in vocab_analysis.items():
            # Use "Bot" instead of "bot" for the bot entry
            display_name = "Bot" if username == "bot" else username
            writer.writerow([
                display_name,
                len(vocab),
                sum(vocab.values()),
                sum(vocab.values()) / len(vocab) if vocab else 0
            ])
    
    # Generate word clouds
    for username, vocab in vocab_analysis.items():
        if username == "bot":
            title = "Bot"
        elif username == "all_users":
            title = "All Users"
        else:
            title = username
        generate_wordcloud(vocab, title)
    
    print(f"\nAnalysis has been saved to: {json_filename}")
    print(f"Statistics have been saved to: {csv_filename}")
    print("Word clouds have been saved as PNG files")


def analyze_game_flow_by_day(db_path):
    """Analyze the game statistics flow by experiment day."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize data structure for each day and round
    days_data = {
        day: {
            'accusations': defaultdict(lambda: defaultdict(int))
        } for day in range(1, 5)
    }
    
    # For each experiment day
    for day in range(1, 5):
        # Analyze rounds 1-10 for each day
        for round_num in range(1, 11):
            cursor.execute('''
                SELECT 
                    COUNT(*) as game_count,
                    SUM(CASE WHEN player1_accusation = 0 AND player2_accusation = 0 THEN 1 ELSE 0 END) as acc_0_0,
                    SUM(CASE WHEN (player1_accusation = 0 AND player2_accusation = 1) OR (player1_accusation = 1 AND player2_accusation = 0) THEN 1 ELSE 0 END) as acc_0_1,
                    SUM(CASE WHEN (player1_accusation = 0 AND player2_accusation = 2) OR (player1_accusation = 2 AND player2_accusation = 0) THEN 1 ELSE 0 END) as acc_0_2,
                    SUM(CASE WHEN player1_accusation = 1 AND player2_accusation = 1 THEN 1 ELSE 0 END) as acc_1_1,
                    SUM(CASE WHEN (player1_accusation = 1 AND player2_accusation = 2) OR (player1_accusation = 2 AND player2_accusation = 1) THEN 1 ELSE 0 END) as acc_1_2,
                    SUM(CASE WHEN player1_accusation = 2 AND player2_accusation = 2 THEN 1 ELSE 0 END) as acc_2_2
                FROM game_analysis
                WHERE game_id / 1000 = ? 
                AND game_round = ?
            ''', (day, round_num))
            
            result = cursor.fetchone()
            
            if result:
                total_games = result[0] or 0
                if total_games > 0:
                    acc_patterns = {
                        "(0, 0)": result[1] or 0,
                        "(0, 1)": result[2] or 0,
                        "(0, 2)": result[3] or 0,
                        "(1, 1)": result[4] or 0,
                        "(1, 2)": result[5] or 0,
                        "(2, 2)": result[6] or 0
                    }
                    days_data[day]['accusations'][round_num] = acc_patterns
    
    conn.close()
    return days_data

def print_accusations_by_day(days_data):
    """Print accusation statistics for each day."""
    accusation_patterns = ["(0, 0)", "(0, 1)", "(0, 2)", "(1, 1)", "(1, 2)", "(2, 2)"]
    pattern_descriptions = {
        "(0, 0)": "No accusations",
        "(0, 1)": "One player accused bot",
        "(0, 2)": "One player accused human",
        "(1, 1)": "Both players accused bot",
        "(1, 2)": "One accused bot, one human",
        "(2, 2)": "Both accused each other"
    }
    
    # Print results for each day
    for day in range(1, 5):
        print(f"\n=== DAY {day} ACCUSATIONS ===")
        print("Round\t" + "\t".join(pattern_descriptions[p] for p in accusation_patterns))
        
        for round_num in range(1, 11):
            row = [str(round_num)]
            for pattern in accusation_patterns:
                count = days_data[day]['accusations'][round_num].get(pattern, 0)
                row.append(str(count))
            print("\t".join(row))
            
def save_accusations_to_csv(days_data, output_file="accusations_by_day.csv"):
    """Save accusation statistics to CSV file."""
    accusation_patterns = ["(0, 0)", "(0, 1)", "(0, 2)", "(1, 1)", "(1, 2)", "(2, 2)"]
    pattern_descriptions = {
        "(0, 0)": "No accusations",
        "(0, 1)": "One player accused bot",
        "(0, 2)": "One player accused human",
        "(1, 1)": "Both players accused bot",
        "(1, 2)": "One accused bot, one human",
        "(2, 2)": "Both accused each other"
    }
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        for day in range(1, 5):
            # Write day header
            writer.writerow([f"Day {day} Accusations"])
            
            # Write column headers
            header = ['Round'] + [pattern_descriptions[p] for p in accusation_patterns]
            writer.writerow(header)
            
            # Write data rows
            for round_num in range(1, 11):
                row = [round_num]
                for pattern in accusation_patterns:
                    count = days_data[day]['accusations'][round_num].get(pattern, 0)
                    row.append(count)
                writer.writerow(row)
            
            # Add blank rows between days
            writer.writerow([])
            writer.writerow([])
    
    print(f"Accusations data has been saved to {output_file}")
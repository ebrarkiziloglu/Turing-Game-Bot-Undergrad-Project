import sqlite3
import json
import pandas as pd
from collections import defaultdict
from typing import List, Tuple, Dict

DAY_1_NAMES = [
    "Gus", "Hal", "Ivy", "Jan", "Kim", "Leo", 
]

DAY_2_NAMES = [
    "Max", "Sam", "Ace", "Ash", "Bea", "Dot",   
]

DAY_3_NAMES = [
    "Eve", "Fay",  "Kit", "Moe", "Pip", "Rex", 
]

DAY_4_NAMES = [
    "Lily", "Abby", "Finn", "Jude", "Noel", "Tess", 
]

NAMES = DAY_1_NAMES + DAY_2_NAMES + DAY_3_NAMES + DAY_4_NAMES

TRIAL_GAMES_OFFSETS = [
    1, 2, 3, 101, 102, 103
]

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

def get_valid_game_ids(db_path: str) -> Dict[str, any]:
    """Modified to return JSON-friendly dictionary instead of printing"""
    conn = sqlite3.connect(db_path)
    all_games_df = pd.read_sql_query(
        "SELECT game_id FROM games WHERE game_id >= 1000 AND game_id < 5000", 
        conn
    )
    conn.close()
    
    all_game_ids = set(all_games_df['game_id'].tolist())
    faulty_games = set(FAULTY_GAMES)
    valid_game_ids = list(all_game_ids - faulty_games)
    
    valid_games_by_day = {str(day): [] for day in range(1, 5)}
    for game_id in valid_game_ids:
        day = get_experiment_day(game_id)
        if day > 0:
            valid_games_by_day[str(day)].append(game_id)
    
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
        
        results = {}
        for key, query in queries.items():
            results[key] = pd.read_sql_query(query, conn)['game_id'].tolist()
        
        cursor = conn.cursor()
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

def analyze_accusations(db_path: str, valid_games_by_day: Dict[str, List[int]]) -> Dict[str, any]:
    """Modified to return JSON-friendly dictionary"""
    pattern_names = {
        "(0, 0)": "No accusations",
        "(0, 1)": "One player accused bot",
        "(0, 2)": "One player accused human",
        "(1, 1)": "Both accused bot",
        "(1, 2)": "One accused bot, one accused human",
        "(2, 2)": "Both accused human"
    }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    all_valid_games = []
    for games in valid_games_by_day["valid_games_by_day"].values():
        all_valid_games.extend(games)
    
    query = """
    SELECT game_id, player1_accused, player2_accused
    FROM games
    WHERE game_id IN ({})
    """.format(','.join('?' * len(all_valid_games)))
    
    cursor.execute(query, all_valid_games)
    results = cursor.fetchall()
    
    overall_patterns = defaultdict(list)
    patterns_by_day = {str(day): defaultdict(list) for day in range(1, 5)}
    
    for game_id, p1_acc, p2_acc in results:
        acc_pattern = normalize_accusation_pair(p1_acc, p2_acc)
        pattern_str = str(acc_pattern)
        
        overall_patterns[pattern_str].append(game_id)
        day = str(game_id // 1000)
        if day in patterns_by_day:
            patterns_by_day[day][pattern_str].append(game_id)
    
    conn.close()
    
    # Calculate statistics
    total_games = len(all_valid_games)
    overall_stats = {
        pattern_str: {
            "pattern_name": pattern_names[pattern_str],
            "percentage": round((len(games) / total_games * 100), 1),
            "count": len(games),
            "game_ids": games,
        }
        for pattern_str, games in overall_patterns.items()
    }
    
    day_stats = {}
    for day, patterns in patterns_by_day.items():
        day_total = sum(len(games) for games in patterns.values())
        day_stats[day] = {
            "total_games": day_total,
            "patterns": {
                pattern_str: {
                    "pattern_name": pattern_names[pattern_str],
                    "percentage": round((len(games) / day_total * 100), 1) if day_total > 0 else 0,
                    "count": len(games),
                    "game_ids": games,
                }
                for pattern_str, games in patterns.items()
            }
        }
    
    return {
        "total_analyzed_games": total_games,
        "overall_patterns": overall_stats,
        "patterns_by_day": day_stats
    }

def analyze_game_durations(db_path: str) -> Dict[str, any]:
    """
    Analyzes game durations using start_time and the minimum of end_time, 
    player1_accusation_time, and player2_accusation_time.
    """
    conn = sqlite3.connect(db_path)
    
    # Use coalesce to handle NULL values and get the minimum end time
    query = """
    SELECT 
        game_id,
        start_time,
        MIN(COALESCE(end_time, datetime('now'))) as end_time,
        MIN(COALESCE(player1_accusation_time, datetime('now'))) as p1_acc_time,
        MIN(COALESCE(player2_accusation_time, datetime('now'))) as p2_acc_time,
        (game_id / 1000) as experiment_day
    FROM games
    WHERE game_id >= 1000 AND game_id < 5000
    GROUP BY game_id
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert times to datetime objects
    for col in ['start_time', 'end_time', 'p1_acc_time', 'p2_acc_time']:
        df[col] = pd.to_datetime(df[col])
    
    # Calculate game duration using minimum of end times
    df['actual_end_time'] = df[['end_time', 'p1_acc_time', 'p2_acc_time']].min(axis=1)
    df['duration_seconds'] = (df['actual_end_time'] - df['start_time']).dt.total_seconds()
    
    # Group by experiment day
    df['experiment_day'] = df['game_id'].apply(lambda x: get_experiment_day(x))
    
    # Prepare results
    durations_by_game = {
        str(row['game_id']): {
            'start_time': row['start_time'].isoformat(),
            'end_time': row['actual_end_time'].isoformat(),
            'duration_seconds': row['duration_seconds'],
            'experiment_day': int(row['experiment_day'])
        }
        for _, row in df.iterrows()
    }
    
    # Calculate statistics
    overall_stats = {
        'average_duration': df['duration_seconds'].mean(),
        'median_duration': df['duration_seconds'].median(),
        'min_duration': df['duration_seconds'].min(),
        'max_duration': df['duration_seconds'].max()
    }
    
    # Calculate statistics by day
    stats_by_day = {}
    for day in range(1, 5):
        day_data = df[df['experiment_day'] == day]['duration_seconds']
        if not day_data.empty:
            stats_by_day[str(day)] = {
                'average_duration': day_data.mean(),
                'median_duration': day_data.median(),
                'min_duration': day_data.min(),
                'max_duration': day_data.max(),
                'game_count': len(day_data)
            }
    
    return {
        'duration_by_game': durations_by_game,
        'overall_statistics': overall_stats,
        'statistics_by_day': stats_by_day
    }


def generate_analysis_json(db_path: str) -> str:
    """
    Generates a complete JSON analysis of the game data.
    """
    # Get valid games first
    valid_games = get_valid_game_ids(db_path)
    
    # Get all analysis results
    analysis_results = {
        "faulty_games": identify_faulty_games(db_path),
        "valid_games": valid_games,
        "accusation_analysis": analyze_accusations(db_path, valid_games),
        "duration_analysis": analyze_game_durations(db_path)
    }
    
    return json.dumps(analysis_results, indent=2)

if __name__ == "__main__":
    db_path = "./turing_chat_server/database/turing.db"
    analysis_json = generate_analysis_json(db_path)
    print(analysis_json)
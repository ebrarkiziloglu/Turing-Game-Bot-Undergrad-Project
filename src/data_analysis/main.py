# main.py
from analysis import analyze_game, get_valid_game_ids, analyze_game_flow, analyze_user_stats, save_user_stats, generate_user_chat_histories, save_vocabulary_analysis
import json, csv
from datetime import datetime


# Find the valid games (per day) and provide detailed statistics per game
def game_stats(db_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"game_analysis_{timestamp}.json"
    
    valid_games = get_valid_game_ids(db_path)
    experiment_days = ["1", "2", "3", "4"]
    
    # Create a dictionary to hold all analyses
    all_analyses = {
        "metadata": {
            "timestamp": timestamp,
            "total_valid_games": valid_games["total_valid_games"],
            "games_per_day": valid_games["valid_games_summary"]
        },
        "games": {}
    }
    
    # Analyze each game and add to the dictionary
    for day in experiment_days:
        for game_id in valid_games['valid_games_by_day'][day]:
            analysis = analyze_game(db_path, game_id)
            if analysis:
                all_analyses["games"][str(game_id)] = analysis
    
    # Write the complete analysis to file
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_analyses, f, indent=2)
    
    print(f"Analysis has been saved to: {output_filename}")

# Save the flow statistic and overall statistic in CSV.
def flow_stats(db_path):
    rounds_data, overall_stats = analyze_game_flow(db_path)
    rounds = list(range(3, 11))
    
    # Extract data
    message_freqs = [rounds_data['message_freq'][r] for r in rounds]
    message_freq_players = [rounds_data['message_freq_players'][r] for r in rounds]
    message_freq_bot = [rounds_data['message_freq_bot'][r] for r in rounds]
    message_lens = [rounds_data['message_len'][r] for r in rounds]
    message_len_players = [rounds_data['message_len_players'][r] for r in rounds]
    message_len_bot = [rounds_data['message_len_bot'][r] for r in rounds]
    game_durations = [rounds_data['game_duration'][r] for r in rounds]
    game_counts = [rounds_data['game_count'][r] for r in rounds]
    accusations = [rounds_data['accusations'][r] for r in rounds]

    print("\n=== FLOW STATISTICS===")
    # Header
    print("Round\tMessage Frequency\tMessage Length\tGame Duration\tGame Count")
    # Data rows
    for i, round_num in enumerate(rounds):
        print(f"{round_num}\t{message_freqs[i]:.2f}\t{message_lens[i]:.2f}\t{game_durations[i]:.2f}\t{game_counts[i]}")
    
    print("\n=== ACCUSATIONS FLOW===")
    # Get all possible accusation patterns
    all_patterns = sorted(list(accusations[0].keys()))  # Using first round's keys
    # Header
    print("Round\t" + "\t".join(all_patterns))
    # Data rows
    for i, round_num in enumerate(rounds):
        row = [str(round_num)]
        for pattern in all_patterns:
            row.append(str(accusations[i].get(pattern, 0)))
        print("\t".join(row))
    
    print("\n=== OVERALL STATISTICS===")
    print("Metric\tValue")
    print(f"Average Message Frequency\t{overall_stats['avg_message_freq']:.2f}")
    print(f"Average Message Frequency of the players\t{overall_stats['avg_message_freq_players']:.2f}")
    print(f"Average Message Frequency of the bot\t{overall_stats['avg_message_freq_bot']:.2f}")
    print(f"Average Message Length\t{overall_stats['avg_message_len']:.2f}")
    print(f"Average Message Length of the players\t{overall_stats['avg_message_len_players']:.2f}")
    print(f"Average Message Length of the bot\t{overall_stats['avg_message_len_bot']:.2f}")
    print(f"Average Game Duration\t{overall_stats['avg_game_duration']:.2f}")
    print(f"Game Count\t{overall_stats['game_count']}")
    
    print("\n=== OVERALL ACCUSATIONS===")
    print("Accusation Pattern\tPercentage")
    for pattern, percentage in overall_stats['accusations'].items():
        print(f"{pattern}\t{percentage:.1f}")

    # 1. Flow statistics CSV
    with open(f'flow_statistics.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Round', 'Message_Frequency', 'Message_Frequency_Players', 'Message_Frequency_Bot', 'Message_Length', 'Message_Length_Players', 'Message_Length_Bot', 'Game_Duration', 'Game_Count'])
        for i, round_num in enumerate(rounds):
            writer.writerow([
                round_num,
                message_freqs[i],
                message_freq_players[i],
                message_freq_bot[i],
                message_lens[i],
                message_len_players[i],
                message_len_bot[i],
                game_durations[i],
                game_counts[i]
            ])
        
        writer.writerow([])
        writer.writerow([])
    
        # 2. Accusations flow:
        # Get all possible accusation patterns
        all_patterns = set()
        for acc_dict in accusations:
            all_patterns.update(acc_dict.keys())
        
        writer = csv.writer(f)
        # Header row with all patterns
        header = ['Round'] + sorted(list(all_patterns))
        writer.writerow(header)
        
        # Data rows
        for i, round_num in enumerate(rounds):
            row = [round_num]
            for pattern in header[1:]:  # Skip 'Round' column
                row.append(accusations[i].get(pattern, 0))
            writer.writerow(row)
    
    # 3. Overall statistics CSV
    with open(f'overall_statistics.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Average Message Frequency (seconds)', f"{overall_stats['avg_message_freq']:.2f}"])
        writer.writerow(['Average Message Frequency Players (seconds)', f"{overall_stats['avg_message_freq_players']:.2f}"])
        writer.writerow(['Average Message Frequency Bot (seconds)', f"{overall_stats['avg_message_freq_bot']:.2f}"])
        writer.writerow(['Average Message Length (characters)', f"{overall_stats['avg_message_len']:.2f}"])
        writer.writerow(['Average Message Length Players (characters)', f"{overall_stats['avg_message_len_players']:.2f}"])
        writer.writerow(['Average Message Length Bot (characters)', f"{overall_stats['avg_message_len_bot']:.2f}"])
        writer.writerow(['Average Game Duration (seconds)', f"{overall_stats['avg_game_duration']:.2f}"])
        writer.writerow(['Game Count', f"{overall_stats['game_count']}"])
    
        writer.writerow([])
        writer.writerow([])

        # 4. Overall accusations:
        writer = csv.writer(f)
        writer.writerow(['Accusation Pattern', 'Percentage'])
        for pattern, percentage in overall_stats['accusations'].items():
            writer.writerow([pattern, f"{percentage:.1f}"])
    
    print(f"CSV files have been generated:")
    print(f"1-2. flow_statistics.csv")
    print(f"3-4. overall_statistics.csv")

if __name__ == "__main__":
    db_path = "./turing_chat_server/database/turing.db"

    game_stats(db_path)
    flow_stats(db_path)

    user_stats, bot_score = analyze_user_stats(db_path)
    save_user_stats(user_stats, bot_score)

    generate_user_chat_histories(db_path)

    save_vocabulary_analysis(db_path)

    days_data = analyze_game_flow_by_day(db_path)
    print_accusations_by_day(days_data)
    save_accusations_to_csv(days_data)

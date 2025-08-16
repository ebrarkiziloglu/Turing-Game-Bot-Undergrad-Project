# bot_detection_experiment_driver.py
import argparse
import random
import logging
import time
from Detector_bot import DetectorBot
from Turing_bot import TuringBot

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='driver.log',     # log to this file
    filemode='a')           # clear the log file each time the program runs

parser = argparse.ArgumentParser(description='Game session driver')
parser.add_argument('-m', '--model_name', type=str, default='llama3.2')
parser.add_argument('-f', '--file_path', type=str, default='game_session.log')
parser.add_argument('-g', '--max_num_of_games', type=int, default=10)
parser.add_argument('-r', '--max_num_of_rounds', type=int, default=10)
args = parser.parse_args()

COLORS = ['Orange', 'Purple', 'Blue', 'Red', 'Green', 'Black']
NUM_OF_COLORS = 6


class DetectorExperimentDriver:
    """GameSessionDriver is an experiment driver that simulates game sessions betweet three bots: a detector bot, and two chatbots. 
    The goal of the experiment is for the detector bot to detect the less-humanlike chatbot among the two chatbots.
    The GameSessionDriver class has the following methods:
    - __init__: Initializes the game session with the detector bot and two chatbots.
    - run_simulation: Runs the game simulation until the maximum number of games is reached.
    - start_game: Starts a new game session with initializing the bots.
    - assign_colors: Assigns random colors to the detector bot, chatbot1, and chatbot2, at the start of a game.
    - initialize_chat_histories: Initializes the chat histories for the detector bot, chatbot1, and chatbot2 with the resepctive colors.
    - send_history_to_detector: Sends the chat history to the detector bot and logs the response.
    - send_history_to_chatbot1: Sends the chat history to chatbot1 and logs the response.
    - send_history_to_chatbot2: Sends the chat history to chatbot2 and logs the response.
    - add_message_to_chat_history: Adds the message to the chat history of the respective bot.
    - get_colors: Returns the colors of the detector bot, chatbot1, and chatbot2.
    - end_game: Ends the game session and logs the detector's analysis.
    - kill_simulation: Kills the game session when the maximum number of games is reached."""

    def __init__(self,
                 detector_prompt_path,
                 chatbot1_prompt_path,
                 chatbot2_prompt_path,
                 model_name: str = 'llama3.2',
                 file_path: str = 'game_session.log',
                 max_num_of_games=10,
                 max_num_of_rounds=10):
        self.log_file = open(file_path, 'a')
        self.colors = {'detector': None, 'chatbot1': None, 'chatbot2': None}
        self.num_of_games = 0
        self.max_num_of_games = max_num_of_games
        self.num_of_rounds = 0
        self.max_num_of_rounds = max_num_of_rounds
        self.game_id = 0
        # self.relative_times = {}
        self.detectors_guess = {}
        self.detectors_guess['chatbot1'] = 0
        self.detectors_guess['chatbot2'] = 0
        self.detectors_target_confidences = {}
        self.detectors_target_confidences['chatbot1'] = 0.0
        self.detectors_target_confidences['chatbot2'] = 0.0
        self.detectors_analysis = {}
        self.detectors_analysis['chatbot1'] = []
        self.detectors_analysis['chatbot2'] = []
        self.detector_chat_history = []
        self.chatbot1_chat_history = []
        self.chatbot2_chat_history = []
        self.detector_bot = DetectorBot(model_name=model_name,
                                        prompt_file_path=detector_prompt_path)
        self.chatbot1 = TuringBot(model_name=model_name,
                                  prompt_file_path=chatbot1_prompt_path)
        self.chatbot2 = TuringBot(model_name=model_name,
                                  prompt_file_path=chatbot2_prompt_path)
        self.send_message_to_bots = [
            self.send_history_to_detector, self.send_history_to_chatbot1,
            self.send_history_to_chatbot2
        ]
        logging.info('Game session initialized.')

    def run_simulation(self):
        if self.num_of_games >= self.max_num_of_games:
            logging.info(
                'Max number of games reached. Killing the game session.')
            return
        else:
            self.start_game()
            self.run_simulation()

    def start_game(self):
        self.game_id += 1
        self.assign_colors()
        logging.info(
            f'Starting the game number {self.game_id} with the following colors: {self.colors}'
        )
        self.log_file.write(f"Game {self.game_id} started: {self.colors}\n")
        self.num_of_games += 1
        self.num_of_rounds = 0
        self.initialize_chat_histories()
        random_int = 0
        init_message = 'Hey guys, what\'s up?'
        response = self.add_message_to_chat_history(0, init_message)
        self.log_file.write(f"### {response}\n")
        while self.num_of_rounds < self.max_num_of_rounds:
            self.num_of_rounds += 1
            random_int2 = random.randrange(2)
            if random_int2 == random_int:
                random_int2 = 2
            random_int = random_int2
            logging.info(
                f'Debug - round {self.num_of_rounds}: Random int: {random_int}'
            )
            self.send_message_to_bots[random_int]()
        self.end_game()

    def assign_colors(self):
        index1, index2, index3 = random.sample(range(NUM_OF_COLORS), 3)
        self.colors['detector'], self.colors['chatbot1'], self.colors[
            'chatbot2'] = COLORS[index1], COLORS[index2], COLORS[index3]

    def initialize_chat_histories(self):
        # self.relative_times[self.game_id] = int(time.time() * 1000) / 1000  # time in seconds
        self.detector_bot.start_game(self.game_id, self.colors['detector'],
                                     self.colors['chatbot1'],
                                     self.colors['chatbot2'])
        self.chatbot1.start_game(self.game_id, self.colors['chatbot1'],
                                 self.colors['detector'],
                                 self.colors['chatbot2'])
        self.chatbot2.start_game(self.game_id, self.colors['chatbot2'],
                                 self.colors['detector'],
                                 self.colors['chatbot1'])

    def send_history_to_detector(self):
        logging.info('Sending chat history to detector.')
        response = self.detector_bot.on_message_groq(
            self.game_id, self.detector_chat_history)
        color = f"{self.colors['detector']}:"
        if not response:
            return
        if response.startswith(color):
            response = response[len(color):].replace('\n', ' ')
        response = self.add_message_to_chat_history(0, response)
        self.log_file.write(f"### {response}\n")
        # self.log_file.write(f"### {self.colors['detector']}: {response}\n")

    def send_history_to_chatbot1(self):
        logging.info('Sending chat history to chatbot1.')
        response = self.chatbot1.on_message_groq(self.game_id,
                                                 self.chatbot1_chat_history)
        color = f"{self.colors['detector']}:"
        if not response:
            return
        if response.startswith(color):
            response = response[len(color):].replace('\n', ' ')
        response = self.add_message_to_chat_history(1, response)
        self.log_file.write(f"### {response}\n")
        # self.log_file.write(f"### {self.colors['chatbot1']}: {response}\n")

    def send_history_to_chatbot2(self):
        logging.info('Sending chat history to chatbot2.')
        response = self.chatbot2.on_message_groq(self.game_id,
                                                 self.chatbot2_chat_history)
        if not response:
            return
        color = f"{self.colors['detector']}:"
        if response.startswith(color):
            response = response[len(color):].replace('\n', ' ')
        response = self.add_message_to_chat_history(2, response)
        self.log_file.write(f"### {response}\n")
        # self.log_file.write(f"### {self.colors['chatbot2']}: {response}\n")

    def add_message_to_chat_history(self, user_index, message):
        roles = {i: 'user' for i in range(3)}
        roles[user_index] = 'assistant'
        # message_time = int(time.time() * 1000) / 1000 - self.relative_times[self.game_id]
        # Create the message content with the color prefix
        if user_index == 0:
            color = self.colors['detector']
        elif user_index == 1:
            color = self.colors['chatbot1']
        else:
            color = self.colors['chatbot2']

        content_withcolor = f"{color}: {message}"
        content_withoutcolor = f"{message}"
        # content_withcolor = f"at time {message_time:.6g}: {color}: {message}"
        # content_withoutcolor = f"at time {message_time:.6g}: {message}"
        
        # Add to all chat histories
        message_obj = []
        for i in range(3):
            content = content_withcolor if i != user_index else content_withoutcolor
            message_obj.append({"role": roles[i], "content": content})
        self.detector_chat_history.append(message_obj[0])
        self.chatbot1_chat_history.append(message_obj[1])
        self.chatbot2_chat_history.append(message_obj[2])
        return content_withcolor

    def get_colors(self):
        return self.detector_color, self.chatbot1_color, self.chatbot2_color

    def end_game(self) -> None:
        analysis = self.detector_bot.end_game_groq(self.game_id)
        try:
            full_analysis = analysis['full_analysis']
            target_color = analysis['target_color'].strip()
            confidence = analysis['confidence']
            if target_color == self.colors['chatbot1']:
                # logging.debug(f'### The bot {self.colors['detector']} accused chatbot1.\n')
                self.detectors_target_confidences['chatbot1'] = (
                    self.detectors_guess['chatbot1'] *
                    self.detectors_target_confidences['chatbot1'] + confidence)
                self.detectors_guess['chatbot1'] += 1
                self.detectors_target_confidences[
                    'chatbot1'] /= self.detectors_guess['chatbot1']
                self.detectors_analysis['chatbot1'].append(full_analysis)
            elif target_color == self.colors['chatbot2']:
                # logging.debug(f'### The bot {self.colors['detector']} accused chatbot2.\n')
                self.detectors_target_confidences['chatbot2'] = (
                    self.detectors_guess['chatbot2'] *
                    self.detectors_target_confidences['chatbot2'] + confidence)
                self.detectors_guess['chatbot2'] += 1
                self.detectors_target_confidences[
                    'chatbot2'] /= self.detectors_guess['chatbot2']
                self.detectors_analysis['chatbot2'].append(full_analysis)
            else:
                logging.error(
                    f"Error: The target color {target_color} is not in the list of colors: {self.colors}"
                )
        except Exception as e:
            full_analysis = analysis
            target_color = None
            confidence = 0.0
            logging.error(
                f"Bot's anaysis does not have the full_analysis value: {e}")
        self.chatbot1.end_game(self.game_id)
        self.chatbot2.end_game(self.game_id)
        self.log_file.write(f"\n### TARGET COLOR: ||{target_color}||\n")
        self.log_file.write(f"### CONFIDENCE: ||{confidence}||\n")
        self.log_file.write(f"### Detector's analysis:\n{full_analysis}\n")
        self.colors = {'detector': None, 'chatbot1': None, 'chatbot2': None}
        self.num_of_rounds = 0
        self.detector_chat_history = []
        self.chatbot1_chat_history = []
        self.chatbot2_chat_history = []
        self.log_file.write(f"Game {self.game_id} ended.\n\n\n")

    def kill_simulation(self, total_time):
        self.log_file.write(
            f"Detector's guess for chatbot1: {self.detectors_guess['chatbot1']}\n"
        )
        self.log_file.write(
            f"Detector's guess for chatbot2: {self.detectors_guess['chatbot2']}\n"
        )
        self.log_file.write(
            f"Target confidence for chatbot1: {self.detectors_target_confidences['chatbot1']}\n"
        )
        self.log_file.write(
            f"Target confidence for chatbot2: {self.detectors_target_confidences['chatbot2']}\n"
        )
        self.log_file.write(
            f"\nDetector's analysis for chatbot1:\n"
        )
        for analysis in self.detectors_analysis['chatbot1']:
            self.log_file.write(f"{analysis}\n")
        
        self.log_file.write(
            f"\nDetector's analysis for chatbot2:\n"
        )
        for analysis in self.detectors_analysis['chatbot2']:
            self.log_file.write(f"{analysis}\n")
        self.log_file.write(f"\nGame session ended in {total_time} seconds.\n\n")
        self.log_file.close()
        logging.info('Killing the game sessions.')


if __name__ == "__main__":
    model_name = args.model_name
    file_path = args.file_path
    max_num_of_games = args.max_num_of_games
    max_num_of_rounds = args.max_num_of_rounds
    detector_prompt_path = "../turing_chat_server/prompts/detector_prompt.txt"
    chatbot1_prompt_path = "../turing_chat_server/prompts/system_prompt.txt"
    chatbot2_prompt_path = "../turing_chat_server/prompts/system_prompt_v00_bad.txt"
    start_time = int(time.time() * 1000) / 1000
    game_session = DetectorExperimentDriver(detector_prompt_path,
                                     chatbot1_prompt_path,
                                     chatbot2_prompt_path, model_name,
                                     file_path, max_num_of_games,
                                     max_num_of_rounds)
    game_session.run_simulation()
    end_time = int(time.time() * 1000) / 1000
    logging.info(f"Total time of the simulation: {end_time - start_time} seconds.")
    game_session.kill_simulation(end_time - start_time)


# ollama:
# python3 bot_detection_experiment_driver.py -m mistral -f game_session1.log -g 1 -r 10
# python3 bot_detection_experiment_driver.py -m gemma2:latest -f game_session1.log -g 1 -r 10

# groq:
# python3 bot_detection_experiment_driver.py -m gemma2-9b-it -f game_session.log -g 1 -r 10
# python3 bot_detection_experiment_driver.py -m mixtral-8x7b-32768 -f game_session.log -g 1 -r 10
# python3 bot_detection_experiment_driver.py -m llama3-8b-8192 -f game_session.log -g 5 -r 10

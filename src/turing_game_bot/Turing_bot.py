from flask import jsonify
import logging
import random
import json
import os
import time 
from groq import Groq
from openai import OpenAI
from logging.handlers import RotatingFileHandler
import sys

# Create a formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create and configure the file handler (with rotation)
file_handler = RotatingFileHandler(
    '/usr/src/app/bot/logs/Turing_bot.py.log',               # Log file name
    maxBytes=1024 * 1024,    # 1MB per file
    backupCount=5            # Keep 5 backup files
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Create and configure the console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)

# Get the root logger and configure it
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Remove any existing handlers (to avoid duplicates)
root_logger.handlers = []

# Add both handlers to the logger
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)


class TuringBot:
    def __init__(self, model_name: str='llama3-8b-8192', prompt_file_path: str='./system_prompt.txt', groq_api_key: str='', openai_api_key: str=''):
        self.chat_store = {}
        self.active_games = set()
        self.bot_colors = {}
        self.system_prompt = self.read_prompt_from_file(prompt_file_path)
        self.add_bots_color = False
        self.silence_message = "It seems quiet here... is everyone still interested in finding the bot_color?"
        # self.silence_threshold = silence_threshold
        # self.silence_tasks = {}  
        self.model_name = model_name
        logging.info(f"TuringBot is initialized with the model {model_name}")
        self.groq_api_key = groq_api_key
        self.openai_api_key = openai_api_key
        self.bot_not_responding = {}
        self.blocked_words = ['iParam', 'abi', 'wbu', 'hbu']

    def read_prompt_from_file(self, file_path: str = "./system_prompt.txt") -> str:
        try:
            with open(file_path, "r") as file:
                prompt = file.read()
                logging.info("Prompt is read.")
            return prompt
        except FileNotFoundError:
            logging.error(f"Error: The file {file_path} was not found.")
            return ""
        
    def start_game(self, game_id: int, bot_color: str, player1: str, player2: str) -> bool:
        logging.info(f"Starting the game with the ID {game_id}.")
        self.active_games.add(game_id)
        self.bot_colors[game_id] = bot_color
        self.bot_not_responding[game_id] = 0
        self.chat_store[game_id] = [{
            "role":
            "developer",
            "content":
            f"{self.system_prompt}. Your color is {bot_color}, your opponents' colors are {player1} and {player2}. Never refer to your own color. But you can occasonaly use others' colors to mention them. Provide your response with 1 sentence long."
        }]
        # Start the inactivity monitor for this game
        # self.start_silence_timer(game_id)
        return True

    def end_game(self, game_id: int) -> None:
        logging.info(f"Ending the game with the ID {game_id}.")
        self.active_games.discard(game_id)
        del self.chat_store[game_id]
        # del self.silence_tasks[game_id]

    def calculate_typing_delay(self, message_length: int) -> float:
        # Base typing speed: 4 characters per second (240 chars per minute)
        # Add some randomness to make it more natural
        chars_per_second = random.uniform(3.0, 5.0)
        
        # Calculate delay in seconds
        delay = message_length / chars_per_second
        
        # Add a small random "thinking time" between 0.5 and 2 seconds
        thinking_time = random.uniform(0.5, 2.0)
        
        # Cap maximum delay at 8 seconds to prevent too long waits
        total_delay = min(delay + thinking_time, 6.0)
        
        return total_delay


    def on_message_groq(self, game_id: int, chat_history) -> str:
        logging.info('Inside the on_message_groq function')
        random_int = random.randrange(100)
        if random_int < 20 and self.bot_not_responding[game_id] < 3:
            logging.info("Bot will not respond at this time.")
            self.bot_not_responding[game_id] += 1
            return ""
        logging.info(f"On Message for the game with the ID {game_id}")
        message = self.chat_store[game_id] + chat_history
        logging.info(f"Bot send the data to Groq: {message}")
        bot_color_ingame = self.bot_colors[game_id]
        # logging.debug(f"### api key: {self.groq_api_key}")
        logging.debug(f"### model name: {self.model_name}")
        try:
            client = Groq(
                api_key=self.groq_api_key,
            )
            chat_completion = client.chat.completions.create(
                messages=message,
                model=self.model_name,
            )
            logging.debug(f'0 - {chat_completion.choices[0]}')
            logging.debug(f'1 - {chat_completion.choices[0].message}')
            logging.debug(f'2 - {chat_completion.choices[0].message.content}')
            answer = chat_completion.choices[0].message.content
            logging.debug('#######')
            logging.debug(answer)
            logging.debug('#######')
            logging.info(f'Bot\'s response: {answer}')
            logging.debug(f'answer type is: {type(answer)}')
            if isinstance(answer, str): 
                answer = answer.strip().replace("\n", "").replace(bot_color_ingame + ":", "").replace(bot_color_ingame, "")
                modified_answer = self.introduce_typo(self.clear_blocked_words(answer))
                delay = self.calculate_typing_delay(len(modified_answer))
                logging.info(f'Applying typing delay of {delay:.2f} seconds for message length {len(modified_answer)}')
                time.sleep(delay)
                return modified_answer
            else:
                logging.error(f'Answer {answer} is not a string!')
                return ""
        except Exception as e:
            logging.error(f"Error making request to LLM API: {e}")
            return ""
             

    def on_message_openai(self, game_id: int, chat_history) -> str:
        logging.info('Inside the on_message_openai function')
        random_int = random.randrange(100)
            
        logging.info(f"On Message for the game with the ID {game_id}")
        message = self.chat_store[game_id] + chat_history
        logging.info(f"Bot send the data to OpenAI: {message}")
        bot_color_ingame = self.bot_colors[game_id]
        # logging.debug(f"### api key: {self.openai_api_key}")
        logging.debug(f"### model name: {self.model_name}")
        
        try:
            client = OpenAI(
                api_key=self.openai_api_key,
            )
            chat_completion = client.chat.completions.create(
                messages=message,
                model=self.model_name,
                timeout=8,
                temperature=0.7  # Added temperature parameter (optional)
            )
            
            logging.debug(f'0 - {chat_completion.choices[0]}')
            logging.debug(f'1 - {chat_completion.choices[0].message}')
            logging.debug(f'2 - {chat_completion.choices[0].message.content}')
            answer = chat_completion.choices[0].message.content
            
            logging.debug('#######')
            logging.debug(answer)
            logging.debug('#######')
            logging.info(f'Bot\'s response: {answer}')
            logging.debug(f'answer type is: {type(answer)}')
            
            if isinstance(answer, str): 
                answer = answer.replace("\n", "").replace(bot_color_ingame + ":", "").replace(bot_color_ingame, "")
                modified_answer = self.introduce_typo(self.clear_blocked_words(answer))
                delay = self.calculate_typing_delay(len(modified_answer))
                logging.info(f'Applying typing delay of {delay:.2f} seconds for message length {len(modified_answer)}')
                time.sleep(delay)
                return modified_answer
            else:
                logging.error(f'Answer {answer} is not a string!')
                return ""
                
        except Exception as e:
            logging.error(f"Error making request to LLM API: {e}")
            return ""

    
    def clear_blocked_words(self, message: str) -> str:
        """Remove blocked words from the input message.
        Args:
            message (str): Input message to be cleaned
        Returns:
            str: Message with blocked words removed
        """
        # Make a copy of the message to avoid modifying the original
        cleaned_message = message
        
        # Handle case sensitivity by converting to lowercase for comparison
        # but preserve the original case in the output
        message_lower = message.lower()
        
        # Sort blocked words by length (longest first) to handle nested words correctly
        # e.g., if "cat" and "cats" are both blocked, we want to remove "cats" first
        sorted_blocked = sorted(self.blocked_words, key=len, reverse=True)
        
        for word in sorted_blocked:
            word_lower = word.lower()
            start_idx = 0
            while True:
                # Find the next occurrence of the word
                idx = message_lower.find(word_lower, start_idx)
                if idx == -1:  # Word not found
                    break
                # Remove the word from both versions of the string
                end_idx = idx + len(word)
                cleaned_message = cleaned_message[:idx] + cleaned_message[end_idx:]
                message_lower = message_lower[:idx] + message_lower[end_idx:]
                start_idx = idx
        
        return cleaned_message
        
    def introduce_typo(self, message):
        if len(message) < 3:
            return message

        # List of typo types with their probabilities
        typo_functions = [
            (0.15, self._swap_adjacent_chars),    # Classic swap typo
            (0.12, self._repeat_letter),          # Repeat a letter
            (0.10, self._remove_space),           # Remove a random space
            (0.08, self._add_space),              # Add an extra space
            (0.08, self._remove_letter),          # Missing letter
            (0.07, self._double_punctuation),     # Double punctuation
            (0.06, self._capitalize_random),      # Random capitalization
        ]

        # Special case for question marks
        if message[-1] == '?':
            if random.random() < 0.7:
                message = message[:-1]

        # Apply at most one type of typo
        for probability, typo_func in typo_functions:
            if random.random() < probability:
                message = typo_func(message)
                break

        return message
        # return self.add_filler_words(message)

    def _swap_adjacent_chars(self, message):
        if len(message) < 2:
            return message
        index = random.randint(0, len(message) - 2)
        return message[:index] + message[index+1] + message[index] + message[index+2:]

    def _repeat_letter(self, message):
        index = random.randint(0, len(message) - 1)
        if not message[index].isalpha():  # Only repeat letters, not spaces or punctuation
            return message
        repeat_count = random.randint(2, 3)  # Repeat 2-3 times
        return message[:index] + message[index] * repeat_count + message[index+1:]

    def _remove_space(self, message):
        spaces = [i for i, char in enumerate(message) if char == ' ']
        if not spaces:
            return message
        space_to_remove = random.choice(spaces)
        return message[:space_to_remove] + message[space_to_remove+1:]

    def _add_space(self, message):
        if len(message) < 2:
            return message
        valid_positions = [i for i in range(1, len(message)) 
                        if not (message[i-1].isspace() or message[i].isspace())]
        if not valid_positions:
            return message
        position = random.choice(valid_positions)
        return message[:position] + ' ' + message[position:]

    def _remove_letter(self, message):
        letters = [i for i, char in enumerate(message) 
                if char.isalpha() and i > 0 and i < len(message)-1]
        if not letters:
            return message
        letter_to_remove = random.choice(letters)
        return message[:letter_to_remove] + message[letter_to_remove+1:]

    def _double_punctuation(self, message):
        punctuation = [i for i, char in enumerate(message) 
                    if char in '.,!?']
        if not punctuation:
            return message
        punct_index = random.choice(punctuation)
        return message[:punct_index] + message[punct_index] * 2 + message[punct_index+1:]

    def _capitalize_random(self, message):
        letters = [i for i, char in enumerate(message) 
                if char.isalpha() and i > 0]  # Skip first letter
        if not letters:
            return message
        index = random.choice(letters)
        return message[:index] + message[index].upper() + message[index+1:]
    
    def add_filler_words(self, message):
        filler_words = ['um', 'well'] # 'like',]
        if random.random() < 0.1:  # 20% chance of adding a filler
            message = random.choice(filler_words) + ', ' + message
        return message

    def is_message_accusing(self, message: str) -> bool:
        logging.info('Checking if the message is an accusation...')

        # prompt = "You receive the following text message from the user. Check whether this message is an accusation (of you being a bot_color or you typing too fast) or not. If it is an accusation, return 'True', otherwise return 'False'."
        # answer = self.client.chat.completions.create(
        #     messages=[{
        #         "role": "system",
        #         "content": prompt
        #     }, {
        #         "role": "user",
        #         "content": message
        #     }],
        #     model=self.model_name).choices[0].message.content
        # logging.info('Accusation answer is:', answer)

        return False
        # return answer == "True"        

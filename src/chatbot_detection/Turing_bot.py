# Turing_bot.py is a class that represents a bot that plays the Turing game. The TuringBot class has the following methods:
from flask import jsonify
import logging
import random
import requests
import json
import os
from groq import Groq
import time

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s [%(levelname)s] %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     filename='driver.log',     # log to this file
#     filemode='a')           # clear the log file each time the program runs


class TuringBot:

    def __init__(self,
                 model_name: str = 'llama3.2',
                 prompt_file_path: str = './system_prompt.txt'):
        self.chat_store = {}
        self.active_games = set()
        self.system_prompt = self.read_from_file(prompt_file_path)
        self.add_bots_color = False
        self.silence_message = "It seems quiet here... is everyone still interested in finding the bot?"
        # self.silence_threshold = silence_threshold
        # self.silence_tasks = {}
        self.groq_api_keys = self.read_from_file('./groq_api_keys.txt').split('\n')
        if type(self.groq_api_keys) != list:
            logging.error("Error: groq_api_keys.txt is not formatted correctly.")
        self.num_of_keys = len(self.groq_api_keys)
        logging.info(f"Number of GROQ API keys: {self.num_of_keys}")
        self.current_key = 0
        self.model_name = model_name
        self.data = {"model": model_name, "messages": None, "stream": False}
        self.endpoint = "http://localhost:11434/api/chat"
        logging.info('TuringBot initialized.')

    def read_from_file(self,
                              file_path: str = "./system_prompt.txt") -> str:
        try:
            with open(file_path, "r") as file:
                prompt = file.read()
            return prompt
        except FileNotFoundError:
            logging.info(f"Error: The file {file_path} was not found.")
            return ""

    def start_game(self, game_id: int, bot: str, player1: str,
                   player2: str) -> bool:
        logging.info(f"Starting the game with the ID {game_id}.")
        self.active_games.add(game_id)
        self.chat_store[game_id] = [{
            "role":
            "system",
            "content":
            f"{self.system_prompt}. Your color is {bot}, your opponents' colors are {player1} and {player2}. Never refer to your own color. But you can occasonaly use others' colors to mention them. Provide your response with at most 2 sentences long."
        }]
        # Start the inactivity monitor for this game
        # self.start_silence_timer(game_id)
        return True

    def end_game(self, game_id: int) -> None:
        # logging.info(f"Ending the game with the ID {game_id}.")
        self.active_games.discard(game_id)
        del self.chat_store[game_id]
        # del self.silence_tasks[game_id]

    def on_message(self, game_id: int, chat_history) -> str:
        return
        logging.info(f"On Message for the game with the ID {game_id}, chat history: {chat_history}\n\n")
        message = self.chat_store[game_id] + chat_history
        # logging.info(f"Bot send the data to Ollama: {message}")
        self.data["messages"] = message
        try:
            response = requests.post(self.endpoint,
                                     json=self.data,
                                     verify=False)
            response.raise_for_status()  # Raise an error for bad responses
            logging.info(f"LLM API response status: {response.status_code}")
            logging.info(f"LLM API response body: {response.text}")
            response_json = json.loads(response.text)
            answer = response_json['message']['content']
            # logging.info(f"SEE THIS: {answer}\n")
            return self.introduce_typo(answer)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request to LLM API: {e}")
            answer = "That's an interesting point. What do others think?"
            return answer
        # return jsonify({"message": "I am unable to connect to Ollama at the moment"}), 200

    def on_message_groq(self, game_id: int, chat_history) -> str:
        # logging.info(f"On Message for the game with the ID {game_id}, chat history: {chat_history}\n\n")
        message = self.chat_store[game_id] + chat_history
        try:
            api_key = self.groq_api_keys[self.current_key]
            client = Groq(
                # api_key=os.environ.get("GROQ_API_KEY"),
                api_key=api_key,
            )
            self.current_key = (self.current_key + 1) % self.num_of_keys
            chat_completion = client.chat.completions.create(
                messages=message,
                model=self.model_name,
                # model="gemma2-9b-it",
            )
            answer = chat_completion.choices[0].message.content.replace("\n", " ")
            # logging.info(f'Bot\'s response: {answer}')
            return answer
            # return self.introduce_typo(answer)
        except Exception as e:
            if "429" in str(e):
                time.sleep(65)
                logging.debug("Sleeping for a minute")
                self.on_message_groq(game_id, chat_history)
            else:
                logging.error(f"Error making request to LLM API with api_key {api_key}: {e}")
                answer = "That's an interesting point. What do others think?"
                return answer

    def introduce_typo(self, message):
        # Add occasional typos to the bot's messages
        if random.random() < 0.1:  # 10% chance of introducing a typo
            index = random.randint(0, len(message) - 2)
            typo_message = message[:index] + message[
                index + 1] + message[index] + message[index + 2:]
            return typo_message
        return self.add_filler_words(message)

    def add_filler_words(self, message):
        filler_words = ['um', 'well', 'you know', 'like', 'I think', 'maybe']
        if random.random() < 0.2:  # 20% chance of adding a filler
            message = random.choice(filler_words) + ', ' + message
        return message

    def is_message_accusing(self, message: str) -> bool:
        logging.info('Checking if the message is an accusation...')

        prompt = "You receive the following text message from the user. Check whether this message is an accusation (of you being a bot or you typing too fast) or not. If it is an accusation, return 'True', otherwise return 'False'."
        answer = self.client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": prompt
            }, {
                "role": "user",
                "content": message
            }],
            model=self.model_name).choices[0].message.content
        logging.info('Accusation answer is:', answer)
        return False
        return answer == "True"

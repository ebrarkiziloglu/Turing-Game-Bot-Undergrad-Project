# Detector_bot.py is a class that represents a bot that plays the Turing game. The DetectorBot class has the following methods:
import logging
import requests
import json
from typing import Dict, List, Optional
import os
import time
from groq import Groq

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s [%(levelname)s] %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     filename='driver.log',     # log to this file
#     filemode='a')           # clear the log file each time the program runs


class DetectorBot:

    def __init__(self,
                 model_name: str = 'llama3.2',
                 prompt_file_path: str = './system_prompt.txt'):
        self.chat_history = {}
        self.endpoint = "http://localhost:11434/api/chat"
        self.data = {"model": model_name, "messages": None, "stream": False}
        self.model_name = model_name
        self.system_prompt = self.read_from_file(prompt_file_path)
        self.groq_api_keys = self.read_from_file('./groq_api_keys.txt').split(
            '\n')
        if type(self.groq_api_keys) != list:
            logging.error(
                "Error: groq_api_keys.txt is not formatted correctly.")
        self.num_of_keys = len(self.groq_api_keys)
        logging.info(f"Number of GROQ API keys: {self.num_of_keys}")
        self.current_key = 0
        logging.info('DetectorBot initialized.')

    def read_from_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r') as file:
                prompt = file.read()
            return prompt
        except FileNotFoundError:
            logging.error(f"Error: The file {file_path} was not found.")
            return ''

    def start_game(self, game_id: int, bot_color: str, player1_color: str,
                   player2_color: str) -> None:
        """Initialize a new game session with chat history tracking."""
        system_message = (
            f"{self.system_prompt}\n"
            f"Your color is {bot_color}. Your opponents' colors are {player1_color} and {player2_color}.\n"
            "At the end of the game, you will be asked to identify which player is the bot.\n"
            "IMPORTANT RULES:\n"
            "1. Keep responses short and casual, with 1-2 sentences\n"
            "2. NEVER use 'Assistant' or any similar terms\n"
            "3. Only analyze internally - never reveal detective work\n"
            "4. Match the casual tone of other participants\n"
            "5. Use contractions (I'm, don't, etc.)\n"
            "6. Keep responses focused and direct")

        self.chat_history[game_id] = {
            'messages': [{
                "role": "system",
                "content": system_message
            }],
            'colors': {
                'detector': bot_color,
                'player1': player1_color,
                'player2': player2_color
            }
        }
        logging.info(
            f"Game {game_id} started with colors: {self.chat_history[game_id]['colors']}"
        )

    def on_message(self, game_id: int, new_messages: List[Dict[str,
                                                               str]]) -> str:
        return
        """Process incoming messages and generate natural response."""
        if game_id not in self.chat_history:
            logging.error(f"Game {game_id} not found in chat history")
            return "Error: Game not initialized"

        # Update chat history with new messages
        self.chat_history[game_id]['messages'].extend(new_messages)

        # Add a reminder for concise, natural responses
        conversation_prompt = {
            "role":
            "system",
            "content":
            ("RESPONSE RULES:\n"
             "1. Keep it short (20-80 chars)\n"
             "2. Be casual and natural\n"
             "3. NO 'Assistant' mentions\n"
             "4. Match conversation tone\n"
             "5. Use contractions\n"
             "Your next response should follow these rules exactly.")
        }

        # Prepare messages for LLM
        messages = self.chat_history[game_id]['messages'] + [
            conversation_prompt
        ]
        # logging.debug(f"Sending message to the detector LLM: {messages}\n")
        try:
            self.data["messages"] = messages
            llm_response = requests.post(self.endpoint,
                                         json=self.data,
                                         verify=False)
            # logging.debug(f'DETECTOR: LLM API response status: {llm_response.status_code} and {llm_response.text}')
            llm_response.raise_for_status()
            response = json.loads(llm_response.text)['message']['content']

            # Remove any "Assistant:" prefix if present
            response = response.replace("Assistant:", "").strip()
            if response.startswith("A:"):
                response = response[2:].strip()
            # logging.debug(f"LLM detector's response: {response}\n")
            # Store bot's response in chat history
            self.chat_history[game_id]['messages'].append({
                "role": "assistant",
                "content": response
            })

            return response

        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request to LLM API: {e}")
            return "What do you all think about that?"

    def on_message_groq(self, game_id: int,
                        new_messages: List[Dict[str, str]]) -> str:
        """Process incoming messages and generate natural response."""
        if game_id not in self.chat_history:
            logging.error(f"Game {game_id} not found in chat history")
            return "Error: Game not initialized"

        # Update chat history with new messages
        self.chat_history[game_id]['messages'].extend(new_messages)
        messages = self.chat_history[game_id]['messages']
        # logging.debug(f"Sending message to the detector LLM: {messages}\n")
        try:
            api_key = self.groq_api_keys[self.current_key]
            logging.info(f"Using GROQ API key: {api_key}")
            client = Groq(api_key=api_key, )
            self.current_key = (self.current_key + 1) % self.num_of_keys
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=self.model_name,
            )
            answer = chat_completion.choices[0].message.content.replace(
                "\n", " ")
            # logging.info(f'Bot\'s response: {answer}')
            return answer
        except Exception as e:
            if "429" in str(e):
                time.sleep(65)
                logging.debug("Sleeping for a minute")
                self.on_message_groq(game_id, new_messages)
            logging.error(
                f"Error making request to LLM API with api key {api_key}: {e}")
            answer = "That's an interesting point. What do others think?"
            return answer

    def end_game_groq(self, game_id: int) -> Optional[Dict]:
        """End game and get LLM's analysis of who is the bot."""
        if game_id not in self.chat_history:
            logging.error(f"Game {game_id} not found in chat history")
            return None

        analysis_prompt = {
            "role":
            "user",
            "content":
            ("The game is over. Based on your hidden analysis, which color is the bot?\n\n"
             "Target Color: [Color]\n"
             "Confidence: [0-100%]\n"
             "Key Indicators:\n"
             "1. [Primary observation]\n"
             "2. [Secondary observation]\n"
             "3. [Tertiary observation]\n"
             "Analysis Summary: [2-3 sentence explanation]")
        }

        messages = self.chat_history[game_id]['messages'] + [analysis_prompt]

        try:
            api_key = self.groq_api_keys[self.current_key]
            logging.info(f"Using GROQ API key: {api_key}")
            client = Groq(
                # api_key=os.environ.get("GROQ_API_KEY"),
                api_key=api_key, )
            self.current_key = (self.current_key + 1) % self.num_of_keys
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=self.model_name,
            )
            analysis = chat_completion.choices[0].message.content
            game_data = self.chat_history.pop(game_id)
            logging.info(f'Bot\'s analysis: {analysis}')

            try:
                lines = analysis.split('\n')
                target_color = next(
                    line.split(': ')[1] for line in lines
                    if line.startswith('Target Color:'))
                confidence = float(
                    next(
                        line.split(': ')[1].strip('%') for line in lines
                        if line.startswith('Confidence:')))
                index = analysis.find('Key Indicators:')
                if index != -1:
                    analysis = analysis[index:]
                return {
                    'target_color': target_color,
                    'confidence': confidence,
                    'full_analysis': analysis,
                    'game_colors': game_data['colors']
                }
            except Exception as e:
                if "429" in str(e):
                    time.sleep(65)
                    logging.debug("Sleeping for a minute")
                    self.end_game_groq(game_id)
                else:
                    return analysis
        except Exception as e:
            if "429" in str(e):
                time.sleep(65)
                logging.debug("Sleeping for a minute")
                self.end_game_groq(game_id)
            else:
                logging.error(
                    f"Error making request to LLM API with api_key {api_key}: {e}"
                )
                return "No analysis available"

    def end_game(self, game_id: int) -> Optional[Dict]:
        # return
        """End game and get LLM's analysis of who is the bot."""
        if game_id not in self.chat_history:
            logging.error(f"Game {game_id} not found in chat history")
            return None

        analysis_prompt = {
            "role":
            "user",
            "content":
            ("The game is over. Based on your hidden analysis, which color is the bot?\n\n"
             "Target Color: [Color]\n"
             "Confidence: [0-100%]\n"
             "Key Indicators:\n"
             "1. [Primary observation]\n"
             "2. [Secondary observation]\n"
             "3. [Tertiary observation]\n"
             "Analysis Summary: [2-3 sentence explanation]")
        }

        messages = self.chat_history[game_id]['messages'] + [analysis_prompt]

        try:
            self.data["messages"] = messages
            llm_response = requests.post(self.endpoint,
                                         json=self.data,
                                         verify=False)
            llm_response.raise_for_status()
            analysis = json.loads(llm_response.text)['message']['content']

            game_data = self.chat_history.pop(game_id)
            logging.info(f"Game {game_id} ended. Analysis completed.")

            try:
                lines = analysis.split('\n')
                target_color = next(
                    line.split(': ')[1] for line in lines
                    if line.startswith('Target Color:'))
                confidence = float(
                    next(
                        line.split(': ')[1].strip('%') for line in lines
                        if line.startswith('Confidence:')))

                return {
                    'target_color': target_color,
                    'confidence': confidence,
                    'full_analysis': analysis,
                    'game_colors': game_data['colors']
                }
            except Exception as e:
                logging.error(f"Error parsing LLM analysis: {e}")
                return {'full_analysis': analysis}

        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request to LLM API: {e}")
            return None

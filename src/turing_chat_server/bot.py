from flask import Flask, request, jsonify
import os
import logging
from turing_game_bot.Turing_bot import TuringBot 

from logging.handlers import RotatingFileHandler
import sys

# Create a formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create and configure the file handler (with rotation)
file_handler = RotatingFileHandler(
    '/usr/src/app/bot/logs/bot.py.log',               # Log file name
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

# prompt is around 5000 char.
# model gemma2-9b-it    ->  15000 token per minute -> 60000 chars per minute
# model llama3-8b-8192  ->  30000 token per minute -> 120000 chars per minute

def read_from_file(file_path: str = "/usr/src/app/groq_api_keys.txt") -> str:
        try:
            with open(file_path, "r") as file:
                prompt = file.read()
                logging.info("Groq API key is read.")
            return prompt
        except FileNotFoundError:
            logging.error(f"Error: The file {file_path} was not found.")
            return ""

app = Flask(__name__)
BOT_PORT = os.getenv("BOT_PORT")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
PROMPT_FILE_PATH="/usr/src/app/turing_chat_server/prompts/system_prompt_casual.txt"
GROQ_API_KEY = read_from_file('/usr/src/app/groq_api_keys.txt').split('\n')[0]
OPENAI_API_KEY = read_from_file('/usr/src/app/openai_api_keys.txt').split('\n')[0]
# logging.debug(f'GROQ_API_KEY: {GROQ_API_KEY}')
# logging.debug(f'OPENAI_API_KEY: {OPENAI_API_KEY}')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

logging.info(f"Model {OPENAI_MODEL_NAME} is being used ppl!")
llm_bot = TuringBot(model_name=OPENAI_MODEL_NAME, prompt_file_path = PROMPT_FILE_PATH, groq_api_key=GROQ_API_KEY, openai_api_key=OPENAI_API_KEY)

@app.route('/start-game', methods=['POST'])
def initialize_game():
    logging.info("Game initialization data received by the bot.")
    data = request.json
    logging.info(f"Received data: {data}") 
    game_id = data.get("game_id")
    bot_color = data.get("botColor")
    player1_color = data.get("player1Color")
    player2_color = data.get("player2Color")
    llm_bot.start_game(game_id, bot_color, player1_color, player2_color)
    return jsonify({"message": "Game initialized successfully"}), 200

@app.route('/response', methods=['POST'])
def bot_response():
    logging.info("Data received by the bot.")
    data = request.json
    logging.info(f"Received data: {data}") 
    game_id = data.get("game_id")
    chat_history = data.get("chat_history")
    logging.info(f"Bot: game_ID is {game_id} and message is {chat_history}")
    # response = llm_bot.on_message_groq(game_id, chat_history)
    response = llm_bot.on_message_openai(game_id, chat_history)
    logging.info(f"bot.py: game {game_id}: The bot\'s response: {type(response)} -> {response}") 
    return response

# add timeout for Ollama connection:
# TODO: Ollama connection still not working..
if __name__ == "__main__":
    logging.info('The bot is active.')

    from gunicorn.app.base import Application

    class GunicornApplication(Application):
        def init(self, parser, opts, args):
            return {
                'timeout': 120,  # Set the timeout to 120 seconds (2 minutes)
                'worker_class': 'sync',
                'workers': 4
            }

        def load(self):
            return app

    GunicornApplication().run()
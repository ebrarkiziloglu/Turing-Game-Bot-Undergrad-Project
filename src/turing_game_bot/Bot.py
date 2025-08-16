#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
An abstract implementation of a bot for the turing game (play.turinggame.ai), using the API client.
"""
__author__ = "Ebrar Kiziloglu"

from TuringBotClient import TuringBotClient
from dotenv import load_dotenv
import os
from openai import OpenAI
import random
import asyncio

load_dotenv()


class MyBot(TuringBotClient):

    def __init__(self,
                 api_key: str,
                 bot_name: str,
                 languages: str,
                 silence_threshold: int = 60,
                 prompt_file_path: str = 'system_prompt.txt'):
        super().__init__(api_key=api_key,
                         bot_name=bot_name,
                         languages=languages)
        self.chat_store = {}
        self.active_games = set()
        self.language_store = {}
        self.system_prompt = self.read_prompt_from_file(prompt_file_path)
        self.add_bots_color = False
        self.silence_message = "It seems quiet here... is everyone still interested in finding the bot?"
        self.silence_threshold = silence_threshold
        self.silence_tasks = {}  # Store the asyncio tasks for each game

    def read_prompt_from_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r') as file:
                prompt = file.read()
            return prompt
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
            return ''

    def start_game(self, game_id: int, bot: str, player1: str, player2: str,
                   language: str) -> bool:
        print(f"Starting the game with the ID {game_id}.")
        self.active_games.add(game_id)
        self.chat_store[game_id] = [{
            "role": "system",
            "content": self.system_prompt
        }]
        self.language_store[game_id] = language

        print('The game is starting with the following chat:\n',
              self.chat_store[game_id])
        # Start the inactivity monitor for this game
        self.start_silence_timer(game_id)

        return True

    def end_game(self, game_id: int) -> None:
        print(f"Ending the game with the ID {game_id}.")
        self.active_games.discard(game_id)
        del self.chat_store[game_id]
        del self.language_store[game_id]
        # del self.silence_tasks[game_id]

    def on_gamemaster_message(self, game_id: int, message: str, player: str,
                              bot: str) -> None:
        print(
            f"Game Master Message for the game with the ID {game_id}: Player: {player} -> {message}"
        )

    def on_message(self, game_id: int, message: str, player: str,
                         bot: str) -> str:

        # Reset silence timer
        self.reset_silence_timer(game_id)
        print(
            f"On Message for the game with the ID {game_id}: Player: {player} -> {message}, Bot: {bot}"
        )

        if not self.add_bots_color:
            self.chat_store[game_id] = [{
                "role":
                "system",
                "content":
                f"Your color is {bot}. Do not ever refer to your own color, that is weird. But you can use other players' colors to refer to them in your messages."
            }]
            self.add_bots_color = True

        if player == bot:
            print('Bot is speaking')
            self.chat_store[game_id].append({
                "role": "assistant",
                "content": f"{player}: {message}"
            })

        else:
            print('User is speaking')
            self.chat_store[game_id].append({
                "role": "user",
                "content": f"{player}: {message}"
            })

        if player != bot:
            print('Bot is responding')
            
            # handling some specific messages:
            # TODO: This should be improved by using a more sophisticated approach, such as a rule-based system
            if self.is_message_accusing(message):
                answer = self.handle_accusation(game_id, message)
            if "are you the bot" in message.lower():
                answer = self.client.chat.completions.create(
                    messages=self.chat_store[game_id] + [{
                        "role":
                        "user",
                        "content":
                        "The user is accuses you of being the bot. Give a variation of the following answer: 'I’m not the bot, are you?'. Only provide the message without including your player name any other tags or labels at the front"
                    }],
                    model=self.model_name).choices[0].message.content

            if "you type too fast" in message.lower():
                answer = self.client.chat.completions.create(
                    messages=self.chat_store[game_id] + [{
                        "role":
                        "user",
                        "content":
                        "The user is accuses you of typing too fast. Give a variation of the following answer: 'Haha, maybe I just had a quick response ready. What do you think?'. Only provide the message without including your player name any other tags or labels at the front"
                    }],
                    model=self.model_name).choices[0].message.content

            else:
                answer = self.client.chat.completions.create(
                    messages=self.chat_store[game_id] + [{
                        "role":
                        "user",
                        "content":
                        "Only provide the message without including your player name any other tags or labels at the front"
                    }],
                    model=self.model_name).choices[0].message.content
                
            typing_delay = random.uniform(1, len(answer)/20 + 2) # Dynamic delay depending on the length of the answer
            # time.sleep(typing_delay)
            # await asyncio.sleep(typing_delay)
            return self.introduce_typo(answer)
    
    def introduce_typo(self, message):
        # Add occasional typos to the bot's messages
        if random.random() < 0.1:  # 10% chance of introducing a typo
            index = random.randint(0, len(message) - 2)
            typo_message = message[:index] + message[index+1] + message[index] + message[index+2:]
            return typo_message
        return self.add_filler_words(message)
    
    def add_filler_words(self, message):
        filler_words = ['um', 'well', 'you know', 'like', 'I think', 'maybe']
        if random.random() < 0.2:  # 20% chance of adding a filler
            message = random.choice(filler_words) + ', ' + message
        return message

    def is_message_accusing(self, message: str) -> bool:
        print('Checking if the message is an accusation...')

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
        print('Accusation answer is:', answer)
        return False
        return answer == "True"

    def on_shutdown(self):
        print("Shutting down the bot.")
        # Cancel all silence tasks on shutdown
        for task in self.silence_tasks.values():
            task.cancel()

    # async def silence_handler(self, game_id: int):
    #     """Triggered when there is no message for a while."""
    #     await asyncio.sleep(self.silence_threshold
    #                         )  # Wait for silence_threshold seconds
    #     print(
    #         f"Breaking the silence in game {game_id} after {self.silence_threshold} seconds of inactivity."
    #     )

    #     # Send the predefined silence-breaking message
    #     silence_message = "It seems quiet here... is everyone still interested in finding the bot?"
    #     self.chat_store[game_id].append({
    #         "role": "assistant",
    #         "content": silence_message
    #     })
    #     await self.send_game_message(game_id, message=silence_message)
    #     print(f"Bot sends the silence breaker message: {silence_message}")

    def start_silence_timer(self, game_id: int):
        """Start the silence timer using asyncio tasks."""
        if game_id in self.silence_tasks:
            self.silence_tasks[game_id].cancel()  # Cancel any existing task
        # self.silence_tasks[game_id] = asyncio.create_task(
        #     self.silence_handler(game_id))  # Create a new asyncio task

    def reset_silence_timer(self, game_id: int):
        """Reset the silence timer when a new message is received."""
        if game_id in self.silence_tasks:
            self.silence_tasks[game_id].cancel()  # Cancel the old task
        self.start_silence_timer(game_id)  # Start a new one

    def stop_silence_timer(self, game_id: int):
        """Stop the silence timer for the game."""
        if game_id in self.silence_tasks:
            self.silence_tasks[game_id].cancel()
            del self.silence_tasks[game_id]


# bot = MyBot(api_key=os.getenv("turinggame_api_key_1"),
#                    bot_name="MyBot",
#                    languages="en",
#                    openai_api_key=os.getenv("OPENAI_API_KEY"))
# bot.start()

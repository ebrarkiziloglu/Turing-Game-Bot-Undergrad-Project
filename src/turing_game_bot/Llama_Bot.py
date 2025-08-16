#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
An initial implementation of a bot for the turing game (play.turinggame.ai), using the API client.
This bot implementation uses the OLLaMA API to generate responses to the user's messages.
"""
__author__ = "Ebrar Kiziloglu"

from Bot import *
import requests
import json

load_dotenv()


class Llama_Bot(MyBot):

    def __init__(self,
                 api_key: str,
                 bot_name: str,
                 languages: str,
                 silence_threshold: int = 60,
                 prompt_file_path: str = 'system_prompt.txt'):
        super().__init__(api_key=api_key,
                         bot_name=bot_name,
                         languages=languages,
                         silence_threshold=silence_threshold,
                         prompt_file_path=prompt_file_path)
        # create a new Llama instance
        self.data = {'model': 'llama3.2', 'messages': None, 'stream': False}
        self.endpoint = "http://localhost:11434/api/chat"

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
            typing_delay = random.uniform(1,
                                          3)  # Delay between 1 and 3 seconds
            # time.sleep(typing_delay)
            # await asyncio.sleep(typing_delay)

            self.data['messages'] = self.chat_store[game_id]
            response = requests.post(self.endpoint,
                                     json=self.data,
                                     verify=False)
            response_json = json.loads(response.text)
            answer = response_json['message']['content']
            # print(f'Answer: {answer}')
            return self.introduce_typo(answer)


llama_bot = Llama_Bot(api_key=os.getenv("turinggame_api_key_2"),
                      bot_name="MyLlamaBot",
                      languages="en")
llama_bot.start()

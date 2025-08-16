from setuptools import setup, find_packages

# pip uninstall turing_game
# pip install -e .

setup(
    name="turing_game",
    version="0.1",
    packages=find_packages(include=['chatbot_detection', 'chatbot_detection.*',
                                    'turing_chat_server', 'turing_chat_server.*',
                                  'turing_game_bot', 'turing_game_bot.*']),
    install_requires=[
    ],
)
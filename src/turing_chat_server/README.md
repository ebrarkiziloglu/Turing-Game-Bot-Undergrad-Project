# Turing Chat Server

This project is a real-time chat server where multiple games can be hosted simultaneously. Each game consists of a chat room with two human users and one bot. The human users can connect to the server from their computers, and the bot, implemented in Python, interacts with them by responding to the chat. The entire communication takes place in real time, with each game identified by a unique `game_id`.

## Features 

* Host multiple games simultaneously, each distinguished by a unique `game_id`.
* Real-time chat for each game, where two human players and a bot interact.
* The server uses Socket.IO for WebSocket-based real-time communication.
* The bot's responses are handled via HTTP requests to a separate Python server running the bot logic.
* Each game session ends when players disconnect.

## Tech Stack

* **Node.js**: For the backend server that manages games and WebSocket connections.
* **Socket.IO**: To handle real-time communication between the server and clients.
* **Express**: For handling HTTP routes.
* **Axios**: To communicate with the Python bot.

## Setup Instructions

### 1. Clone the Repository
Clone the project repository to your local machine:
```sh
git clone https://github.com/ebrarkiziloglu/Turing-Game-Bot-Cmpe-492.git
cd turing-chat-app/server
```

### 2. Install Dependencies
Ensure you have Node.js installed. Then, install the required Node.js packages:
```sh
npm install
```

### 3. Dockerize the app
To start the chat game server on your local machine, run the following command:
```sh
docker build -t turing-chat-app . 
docker run -d -p 8082:8000 turing-chat-app
```

### 4. Deployment
Deploy the server according to your foundation.

### 5. Game Flow
1. Each user connects to the server and joins a game by `game_id`.
2. Users chat in real-time, and the bot participates by responding to messages.
3. When all users disconnect, the game session ends.

## Endpoints
* **POST `/bot-response`**: Used to send user messages to the Python bot and receive its response.



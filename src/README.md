# 🚀 Source Code - LLM-driven Turing Game Bot

This directory contains the complete source code for the LLM-driven Turing Game Bot project. The project is structured as a multi-component system with bot detection experiments, chat server, and intelligent bot implementations.

## 🏗️ Project Architecture

The project consists of three main components:

### 🌐 **Turing Chat Server** (`turing_chat_server/`)
Web-based chat server for hosting Turing game sessions:
- **`server.js`** - Node.js backend server
- **`chatroom.html`** - Main chat interface
- **`gameentry.html`** - Game entry and setup interface
- **`bot.py`** - Python bot integration
- **`database/`** - SQLite database schemas and data
- **`prompts/`** - System prompts for different bot personalities

### 🧠 **Turing Game Bot** (`turing_game_bot/`)
Core bot implementations with LLM integration:
- **`Turing_bot.py`** - Main bot class with advanced features
- **`Bot.py`** - Base bot implementation
- **`Llama_Bot.py`** - Local LLM integration using Llama models

### 🤖 **Chatbot Detection** (`chatbot_detection/`)
Experimental framework for testing bot detection capabilities:
- **`Detector_bot.py`** - Bot detection logic and algorithms
- **`Turing_bot.py`** - Core Turing game bot implementation
- **`bot_detection_experiment_driver.py`** - Main experiment runner
- **`game_session.log`** - Detailed game session logs

### 📊 **Data Analysis** (`data_analysis/`)
Comprehensive analysis tools and data processing:
- **`analysis.py`** - Main analysis engine (1190 lines)
- **`game_analysis.py`** - Game-specific analysis functions
- **`main.py`** - Analysis pipeline entry point
- **Various CSV/JSON files** - Game statistics and user data
- **`user_chats/`** - Individual user conversation logs
- **`user_wordclouds/`** - Generated word cloud visualizations

## 🐳 Docker & Deployment

### Containerization
- **`docker-compose.yml`** - Multi-service orchestration
- **`Dockerfile-server`** - Chat server container
- **`Dockerfile-bot`** - Bot service container
- **`nginx.conf`** - Reverse proxy configuration

### Services
- **Nginx** (Port 80) - Reverse proxy and load balancer
- **Server** (Port 8081) - Main chat server
- **Bot** (Port 8005) - Bot service with health checks

## 🛠️ Setup & Installation

### Prerequisites
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for chat server)
cd turing_chat_server
npm install

# Install the package in development mode
pip install -e .
```

### Environment Variables
- `GROQ_MODEL_NAME` - Local LLM model (default: llama3-8b-8192)
- `OPENAI_MODEL_NAME` - OpenAI model (default: gpt-4o)
- `BOT_PORT` - Bot service port (default: 8005)
- `SERVER_PORT` - Chat server port (default: 8081)

### Quick Start
```bash
# Start all services with Docker
docker-compose up -d

# Or run components individually
python -m chatbot_detection.bot_detection_experiment_driver
cd turing_chat_server && node server.js
python -m turing_game_bot.Turing_bot
```

## 🔧 Key Features

### Bot Capabilities
- **Human-like conversation** - Advanced prompt engineering
- **Multiple personalities** - Configurable bot behaviors
- **LLM integration** - Support for local and cloud models
- **Learning capabilities** - Performance improvement over time

### Server Features
- **Real-time chat** - WebSocket-based communication
- **Game management** - Session creation and monitoring
- **User authentication** - Username-based login system
- **Database persistence** - SQLite storage for games and messages

### Analysis Tools
- **Game statistics** - Comprehensive performance metrics
- **User behavior analysis** - Conversation pattern recognition
- **Vocabulary analysis** - Linguistic pattern detection
- **Visualization** - Word clouds and statistical charts

## 📁 File Structure

```
src/
├── chatbot_detection/          # Bot detection experiments
├── turing_chat_server/         # Web chat server
├── turing_game_bot/           # Core bot implementations
├── data_analysis/             # Analysis and data processing
├── docker-compose.yml         # Service orchestration
├── requirements.txt           # Python dependencies
├── setup.py                  # Package configuration
└── nginx.conf               # Web server configuration
```

## 🚀 Running Experiments

### Bot Detection Tests
```bash
cd chatbot_detection
python bot_detection_experiment_driver.py
```

### Data Analysis
```bash
cd data_analysis
python main.py
python analysis.py
```

### Web Interface
1. Start the server: `docker-compose up`
2. Open browser to `http://localhost`
3. Navigate to game entry page
4. Start a new Turing game session

## 🔍 Development Notes

- **Python 3.8+** required for bot components
- **Node.js 16+** required for chat server
- **SQLite** database for data persistence
- **Docker** recommended for full deployment
- **Health checks** implemented for bot service

## 📊 Performance Monitoring

The system includes comprehensive logging and monitoring:
- Game session logs in `chatbot_detection/`
- Server logs in `turing_chat_server/logs/`
- Bot health checks via HTTP endpoints
- Database query logging and performance metrics

---

*This is the core source code for the LLM-driven Turing Game Bot project, implementing a complete system for human-AI interaction studies and bot detection research. This README is generated by an LLM.*

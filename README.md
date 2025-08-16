# 🤖 CMPE 492 - LLM-driven Turing Game Bot

> *"Can you tell if you're talking to a human or an AI?"* 🧠

This repository contains my **Senior Project** ([CMPE 492](https://cmpe.bogazici.edu.tr/courses/cmpe492/)) at **Boğaziçi University**, supervised by [Suzan Üsküdarlı](https://uskudarli.gitlab.io/uskudarli-academic/) and [Onur Güngör](https://www.cmpe.boun.edu.tr/tr/people/onur.g%C3%BCng%C3%B6r).  

---

## 📋 Table of Contents
- [🎯 About the Project](#-about-the-project)
- [🏆 Key Results](#-key-results)
- [🚀 Future Work](#-future-work)
- [🛠️ Tools & Technologies](#️-tools--technologies)
- [📁 Project Structure](#-project-structure)
- [📊 Documentation & Reports](#-documentation--reports)
- [👨‍💻 About Me](#-about-me)
- [📞 Contact](#-contact)

---

## 🎯 About the Project

The goal of this project was to develop an **intelligent chatbot** capable of playing the [Turing Game](https://www.turinggame.ai/), where users attempt to distinguish humans from AI participants.  

### 🔑 Key Features of the Bot:
* 🗣️ Engages in **natural, human-like conversations**  
* 🧠 Uses a **Large Language Model (LLM)** to improve performance over time  
* 🎭 Successfully **deceived at least one human in 31% of sessions** during evaluation  
* 🔄 **Adaptive learning** capabilities for continuous improvement
* 🌍 **Multi-language support** for diverse user interactions

For more details, see the [official project description](https://www.cmpe.boun.edu.tr/content/project-title-llm-driven-turing-game-bot).  

![cover](.github/banner.png)  
*Image credit: OpenAI, 2024*

---

## 🏆 Key Results

### 📈 Performance Metrics
* 🎮 **93 valid Turing Game sessions** conducted successfully
* 🎭 **31% deception rate** - bot successfully deceived at least one human per session
* 👥 **0.49 persons per session** deceived on average
* 🎯 **Surpassed minimum target** of 20% by 11 percentage points
* ⚡ **System stability** maintained with only 27 sessions excluded due to technical issues

### 🔍 Analysis Insights
* 📊 **Detectable patterns** identified in message length, vocabulary, and conversation flow
* 🎨 **Clear directions** for future improvements in:
  - Naturalness enhancement
  - Topic transition optimization
  - Multilingual code-switching capabilities

For comprehensive details into the results of my study, [📖 read the final report](reports/492_final_report.pdf).  

---

## 🚀 Future Work

Planned improvements include:

### 🎨 **Enhanced Bot Capabilities**
- 🎭 **Advanced prompt design** for more varied and human-like responses  
- 👥 **Multi-user game formats** for richer interaction dynamics
- 🤔 **"I cannot decide" option** for more realistic human behavior
- ⏱️ **Turn-taking controls** for structured conversation flow

### 🌍 **Expanded Testing & Analysis**
- 🗣️ **Native English speaker testing** for comparative analysis
- 🌐 **Multi-language support** expansion
- 📊 **Advanced analytics** for deeper pattern recognition
- 🔬 **A/B testing** for prompt optimization

---

## 🛠️ Tools & Technologies

### 💻 **Programming Languages & Frameworks**
* 🐍 **Python** - Core bot logic and analysis
* 🟢 **Node.js** - Web server and real-time communication
* 🗄️ **SQLite** - Data persistence and game storage

### 🤖 **AI & Machine Learning**
* 🧠 **OpenAI GPT-4o** - Primary LLM for bot responses
* 🦙 **Local LLM models** - Llama integration for offline capabilities
* 🔌 **API-based communication** - Seamless model switching

### 🐳 **Deployment & Infrastructure**
* 🐳 **Docker** - Containerized deployment
* 🌐 **Nginx** - Reverse proxy and load balancing
* 📊 **Real-time WebSocket** - Live chat functionality

---

## 📁 Project Structure

```
Turing-Game-Bot-Undergrad-Project/
├── 🤖 src/                    # Core source code
│   ├── chatbot_detection/     # Bot detection experiments
│   ├── turing_chat_server/    # Web chat server
│   ├── turing_game_bot/       # Bot implementations
│   ├── data_analysis/         # Analysis tools
|   └── 🐳 docker-compose.yml  # Deployment configuration
├── 📊 reports/                # Research documentation
│   ├── 492_final_report.pdf   # Complete project report
│   └── analytics/             # Data analysis & visualizations
├── 📚 docs/                   # Project documentation
│   ├── diagrams/              # System architecture
│   └── screenshots/           # UI mockups & examples
└── project_poster.pdf                 # Project presentation
```

---

## 📊 Documentation & Reports

### 📖 **Academic Reports**
- [📋 Final Report](reports/492_final_report.pdf) - Complete project analysis and results
- [🎨 Project Poster](./project_poster.pdf) - Visual project overview

### 📈 **Analytics & Data**
- [📊 Analytics README](reports/analytics/README.md) - Data analysis overview
- [🔍 Source Code README](src/README.md) - Technical implementation guide

### 🏗️ **System Architecture**
- [📐 UML Diagrams](docs/diagrams/) - Class, deployment, and use case diagrams
- [🖼️ UI Screenshots](docs/screenshots/) - Application interface examples

---

## 👨‍💻 About Me

I am a **senior Computer Engineering student** at **Boğaziçi University, Turkey**. My passion lies in **Natural Language Processing applications** and exploring the fascinating realm of **Machine Learning**. I actively seek opportunities to train machines and push the boundaries of AI-human interaction.

### 🎓 **Academic Focus**
- 🧠 **Natural Language Processing** - Core research interest
- 🤖 **Machine Learning** - Algorithm development and optimization
- 🔬 **AI Research** - Human-AI interaction studies
- 💻 **Software Engineering** - Full-stack development expertise

---

## 📞 Contact

### 🔗 **Professional Links**
- 👔 [LinkedIn](https://www.linkedin.com/in/ebrarkiziloglu/)
- 📧 [Email](mailto:ebrarkiziloglu@gmail.com)
- 🏫 [Boğaziçi University](https://www.boun.edu.tr/)

### 💬 **Get in Touch**
Feel free to reach out for:
- 🤝 **Collaboration opportunities** in NLP/AI research
- 💡 **Project discussions** and idea sharing
- 📚 **Academic guidance** and mentorship
- 🚀 **Career opportunities** in AI/ML field

---

## ⭐ **Star This Repository**

If you find this project interesting or useful, please consider giving it a ⭐ star! It helps with visibility and encourages further development.

---

*This project represents the culmination of my undergraduate studies in Computer Engineering, exploring the fascinating intersection of human behavior, artificial intelligence, and natural language processing. The results demonstrate the potential for creating more human-like AI systems while highlighting areas for future improvement. This README is written with the help of an LLM.* 🎓✨
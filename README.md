# 🤖 Test Simple Bot
> Flashcards • Event Scheduling • Personal Reminders — Built for Discord

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-blueviolet)](https://discordpy.readthedocs.io/en/stable/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ About

**Test Simple Bot** is a lightweight Discord bot designed for:
- 📚 Creating and studying flashcards
- 🗓️ Managing server events
- 🔔 Setting personal reminders

Perfect for productivity servers, study groups, or anyone who wants a smarter Discord workspace.

---

## 📋 Features

| Category    | Command | Description |
| :---------- | :------ | :---------- |
| **Flashcards** | `!createFlashcard [topic] [question] [answer]` | Create a new flashcard |
|  | `!listFlashcards [optional topic]` | View flashcards, optionally filter by topic |
|  | `!deleteFlashcard [topic] [question]` | Delete a flashcard |
|  | `!quizme [topic]` | Take a flashcard quiz (sent via DM) |
| **Events** | `!createEvent [name] [MM/DD/YYYY] [HH:MM]` | Schedule a server event |
|  | `!listEvents` | View all upcoming events |
|  | `!deleteEvent [name or ID]` | Cancel an event |
| **Reminders** | `!createReminder [name] [MM/DD/YYYY] [HH:MM]` | Set a personal DM reminder |
|  | `!listReminders` | View all your active reminders |
|  | `!deleteReminder [name]` | Delete a reminder |
| **General** | `!commandHelp` | Display full command list |

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.8+
- [discord.py](https://pypi.org/project/discord.py/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [pytz](https://pypi.org/project/pytz/)

Install dependencies:
```bash
pip install discord python-dotenv pytz

2. Setup
	1.	Clone this repository:
git clone https://github.com/yourusername/test-simple-bot.git
cd test-simple-bot
	2.	Create a .env file in the root folder:
TOKEN=your_discord_bot_token
	3.	Run the bot:
python your-bot-file.py

3. Permissions

Make sure the bot has the following Discord permissions:
	•	Read Messages / Send Messages
	•	Manage Events
	•	Send Direct Messages

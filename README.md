# Stark-Data-Analyst

## Overview

**Stark-Data-Analyst** is a cutting-edge Slackbot, powered by AI and GPT, designed to serve as your personalized data analyst. It integrates seamlessly into Slack, enabling users to ask questions, analyze datasets, and generate insights in real time—all without leaving their workspace.

## Features

- **Interactive Slack Integration**: Communicate with the bot directly through Slack mentions and messages.
- **AI-Powered Insights**: Harness the capabilities of GPT-4 for natural language queries and advanced data analysis.
- **Seamless Data Loading**: Supports data from AWS S3 or local CSV files, making it adaptable to different workflows.
- **Slack-Optimized Output**: Converts complex tables and insights into Slack-friendly formats for easy consumption.
- **Extensible and Scalable**: Designed with modularity in mind, making it easy to extend functionalities.

---------------------------------

## How to create your own slackbot

To integrate the slack bot, there are 4 important components:
1. Python Environment and Code Setup
2. Slack Setup
3. OpenAI API Configuration
4. Hosting & Testing


### 1. Python Environment and Code Setup

#### Clone the Repository

Begin by cloning the repository from GitHub:

```bash
git clone https://github.com/Vanshaj5101/Stark-Data-Analyst.git
cd Stark-Data-Analyst
```

The repository contains the following key files:

**Quart_app.py**: The main Python file that holds the Quart application to manage Slack events.
**slack_bot_handler.py**: Contains all the bot logic. Events received by Quart_app.py are processed here to interpret user requirements and provide outputs.
**FetchUserId.py**: A utility script to fetch the Slack bot's user ID.
**requirements.txt**: Lists all dependencies for the project.
**data.csv**:A dummy dataset for testing the bot's data analysis functionality.

After cloning the repo, first configure environment variables and virtual environment

#### Configure Environment Variables
Create a .env file in the project directory with the following structure:
```
SLACK_BOT_TOKEN=<your-slack-bot-token>
SLACK_BOT_USER_ID=<your-slack-bot-user-id>
OPEN_AI_API_KEY=<your-openai-api-key>
WEB_TOKEN=<your-web-token>
```



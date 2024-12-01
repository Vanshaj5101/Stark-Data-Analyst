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


## 1. Python Environment and Code Setup

#### -- Clone the Repository

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

#### -- Configure Environment Variables
Create a .env file in the project directory with the following structure: 

(we will look into steps to get values for all the environment variables, for now have this structure copied and pasted as .env file)
```
SLACK_BOT_TOKEN=<your-slack-bot-token>
SLACK_BOT_USER_ID=<your-slack-bot-user-id>
OPEN_AI_API_KEY=<your-openai-api-key>
WEB_TOKEN=<your-web-token>
```

#### -- Setup Python Virtual Environment

```
python3 -m venv .venv
source .venv/bin/activate
```
Install required dependencies:
```
pip install -r requirements.txt
```


## 2. Slack Setup

Follow these steps to configure the Slack app:

### Step 1: Create a Slack App
1. Visit [Slack API Apps](https://api.slack.com/apps).
2. Click **"Create New App"**.
3. Select the **"From scratch"** option.
4. Provide an **App Name** and select your Slack workspace.
5. Click **Create App**.

### Step 2: Add Required Permissions
1. Navigate to the **OAuth & Permissions** section in the left-hand menu.
2. Under **Scopes**, add the following bot token scopes:
   - `app_mentions:read`
   - `channels:history`
   - `chat:write`
   - `chat:write.public`
   - `files:read`
   - `incoming-webhook`

### Step 3: Install the App
1. Go to the **Install App** section in the left-hand menu.
2. Click **Install App to Workspace**.
3. Copy the **OAuth Token** from the app after installation and update your `.env` file:
   ```env
   SLACK_BOT_TOKEN=<your-slack-bot-token>

### Step 4: Get Web Token
1. Go to the **Basic Information** section in the left-hand menu.
2. Scroll down to **App-Level Tokens** section.
3. Click **Generate Token**
4. Enter following details:
   - Token Name: WebToken
   - Scope: connections:write
5. Click Generate to create the Web Token.
6. Copy the generated token and update your .env file:
```
WEB_TOKEN=<your-web-token>
```
### Step 5: Get Slack Bot User Id
1. Run **FetchUserId.py** file
   ```
   python3 FetchUserId.py
   ```
2. Response will look like: we need **user_id**
   ```
      {
        "ok": true,
        "url": "https://your-workspace.slack.com/",
        "team": "Your Team",
        "user": "your-slack-bot-user-id",
        "user_id": "your-slack-bot-user-id"
      }
   ```
3. Update .env file
   ```
   SLACK_BOT_USER_ID=<your-slack-bot-user-id>
   ```


## 3. Open AI API Configuration

### Step 1: Sign Up or Log In
1. Visit [OpenAI's official website](https://platform.openai.com/).
2. If you don't have an account, click on "Sign up" to create one. If you already have an account, simply log in.

### Step 2: Navigate to the API Keys Section
1. Once logged in, go to the [API Keys page](https://platform.openai.com/account/api-keys).
2. If you're using OpenAI for the first time, you may need to create an organization (follow the prompts on the site).

### Step 3: Generate the API Key
1. On the API Keys page, click on the button **Create new secret key**.
2. This will generate a new API key.
3. Copy the generated API key and keep it secure (you will not be able to view the key again once you close this window).

### Step 4: Update `.env` File
1. Open your `.env` file in the project directory.
2. Add the OpenAI API key:
   ```env
   OPEN_AI_API_KEY=<your-openai-api-key>
   ```
## 4. Hosting and Testing

In order to have your user interact with your slack bot, you need to host your python program as a server. 

Now for testing, we can have local server, but while in production we need authorized server like server running on AWS cloud services.

For Hosting, there are two important steps:

1. Exposing your code server to communicate with Slack
     a. Local Hosting
     b. Hosting on AWS
2. Configuring Slack Bot to listen all the app mentions

### Local Hosting:

#### Test the Slackbot Locally with ngrok

Once you've set up the code, the next step is to test your Slackbot locally. We'll use **ngrok** to expose your local server to the public, so that Slack can send events to your local machine.

### Step 1: Install ngrok

If you don't have **ngrok** installed yet, follow these steps:

1. Go to [ngrok's website](https://ngrok.com/).
2. Sign up for a free account.
3. Download and install ngrok for your operating system.
4. After installing, authenticate ngrok using the following command:
   ```bash
   ngrok authtoken <your-ngrok-auth-token>
   ```
   
### Step 2: Run your local server

In your project directory, run the Quart application:

```
python3 Quart_app.py
```
By default, your local server will be running on http://127.0.0.1:3081. You can change the port in your code if needed.

### Step 3: Expose your local server using ngrok

Open a new terminal window and run the following command to expose your local server to the public:
```
ngrok http 3081
```
ngrok will give you a **forwarding link** like the one in example:
```
Forwarding                    https://07de-129-219-8-84.ngrok-free.app -> http://localhost:3081
```
Copy this link and reach out to https://api.slack.com/apps

In the Slack app interface, reach out to the Slack Bot you created:
1. Under Event Subscription menu from the left hand side menu
2. Toggle the Event Subscription button to "On" state
3. Add the forwarding link provided by ngrok with "/slack/events" as suffix to it
   ```
   <your-ngrok-link>/slack/events
   ```
4. Under Subscribe to Bot events, subscribe your bot to listen "app_mention"
5. Adding the public link to **_Request URL_** part will trigger a challenge event by Slack to verify the link.

Slack Link Check - We’ll send HTTP POST requests to this URL when events occur. As soon as you enter a URL, we’ll send a request with a challenge parameter, and your endpoint must respond with the challenge value. 

This will now allow your code running on your local machine to interact with Slack APIs.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/b749142f-53a0-44e9-b63a-9323d38e5e2c">


## 5. Testing Bot in Slack

Reach out to any slack communication channel and run the following comment:
```
/invite @SlackBotName
```

You will have your slack bot added to the communication channel.

Usage:
```
@slackbotname Give me total number of enrollments
```

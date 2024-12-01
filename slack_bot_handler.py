import logging
import os
from dotenv import find_dotenv, load_dotenv
import requests
from langchain.agents.agent_types import AgentType

# from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
import boto3
from io import StringIO
import pandas as pd
from boto3.dynamodb.conditions import Key
import time

# Load environment variables from a .env file (if it exists)
# .env files holds the below variables and secret keys
load_dotenv(find_dotenv(), override=True)

# Fetch required environment variables for authentication and configuration
# These environment variables are essential for secure communication with Slack's API and OpenAI services.

# 1. SLACK_BOT_TOKEN:
#    - The OAuth token for your Slack bot, which is used to authenticate API requests.
#    - Allows the bot to interact with Slack channels, users, and messages on your workspace.
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

# 2. SLACK_SIGNING_SECRET:
#    - A secret key used to verify that incoming requests to your server are genuinely from Slack.
#    - Helps prevent unauthorized access by ensuring that only Slack's events are processed.
# SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# 3. SLACK_BOT_USER_ID:
#    - The unique ID assigned to your Slack bot when it's installed in a workspace.
#    - Useful for identifying the bot itself during conversations to avoid responding to its own messages.
SLACK_BOT_USER_ID = os.environ["SLACK_BOT_USER_ID"]

# 4. OPEN_AI_API_KEY:
#    - The API key for accessing OpenAI's GPT models, which powers the AI assistant's natural language processing capabilities.
#    - Enables the bot to generate responses, answer questions, or handle complex queries based on AI processing.
OPEN_AI_API_KEY = os.environ["OPEN_AI_API_KEY"]

# 5. SLACK_BASE_URL:
#    - The base URL for sending messages to Slack via their Web API.
#    - Specifically used for posting messages to channels, threads, or direct messages.
SLACK_BASE_URL = "https://slack.com/api/chat.postMessage"


# AWS S3 Configuration:
# These variables are used for storing and retrieving data from an S3 bucket.
# 1. S3_BUCKET_NAME:
#    - The name of the S3 bucket where data will be stored.
S3_BUCKET_NAME = "starkslackbot"

# 2. S3_FILE_NAME:
#    - The specific file within the S3 bucket where data (like learner information) is stored.
S3_FILE_NAME = "Learner Data.csv"


class SlackBotHandler:
    def __init__(self) -> None:
        """
            Initializes the SlackBotHandler class.

            This method sets up various components required for interacting with Slack,
            OpenAI, and AWS services. It also initializes variables to store data for handling
            incoming Slack events and processing learner data.
        """
        self.logger = logging.getLogger()     # Set up a logger instance for logging messages throughout the class.
        self.slack_url = SLACK_BASE_URL # Slack API URL for sending messages to channels or users.
        self.s3 = boto3.client("s3", region_name="us-east-1") # The S3 client is used to upload, download, and manage files in the specified S3 bucket.
        self.learner_data = pd.DataFrame() # Initialize an empty pandas DataFrame to store learner data.

        # Set up the OpenAI LLM (Language Learning Model) for generating responses.
        # Using the ChatOpenAI class from the OpenAI library to interact with the GPT-4 model.
        # `temperature=0` ensures that the responses are deterministic (i.e., less random).
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o", api_key=OPEN_AI_API_KEY)
        self.df_agent = ""
        self.client_msg_id = ""  # Stores the ID of the client message to track and prevent duplicate processing
        self.event_id = ""  # Stores the Slack event ID to ensure that each event is processed only once.

    def handle_app_mention(self, body):
        """
            Handles Slack 'app_mention' events.

            This method is triggered when a user mentions the bot in a Slack channel. It processes the event by:
            1. Sending a confirmation message to Slack indicating that the bot is working on the request.
            2. Loading data from an S3 bucket into a pandas DataFrame.
            3. Creating a Pandas DataFrame Agent using OpenAI's GPT model to generate insights.
            4. Extracting the user's question from the Slack message, generating a relevant response,
            and posting the results back to Slack.

            Arguments:
                body (dict): The JSON payload received from Slack containing event details.

            Returns:
                None: Sends a response directly to Slack with the generated insights.
        """

        # Send an initial "processing" message to Slack to inform the user
        self.send_processing_message(body=body)

        # Load data from the specified S3 bucket into a pandas DataFrame.
        # self.load_data_from_s3()
        self.load_data_from_csv('data.csv')

        #  # Step 3: Create a DataFrame agent using OpenAI's GPT-4 model.
        # The agent will analyze the data and generate responses based on user questions.
        df_agent = create_pandas_dataframe_agent(
            llm=self.llm,
            df=self.learner_data,
            # verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
        )

        # Step 4: Store identifiers for the current Slack message and event
        # to ensure each event is processed uniquely.
        self.client_msg_id = body["event"]["client_msg_id"]
        self.event_id = body["event_id"]

        try:
            # Step 5: Extract the user's question from the Slack message text.
            # The bot was mentioned, so we strip the mention from the message.
            text = body["event"]["text"]
            mention = f"<@{SLACK_BOT_USER_ID}>"
            text = text.replace(mention, "").strip()

            # Step 6: Construct a prompt for the DataFrame agent to generate relevant data.
            user_question = f"""
                Question : {text}
                Instruction : output should be well formatted pivot table. Consider complete dataset and result should be accurate
            """
            relevant_data = df_agent.invoke(user_question)["output"]

            # Step 7: Create a detailed prompt for the GPT model to generate insights.
            # It uses the extracted data to generate a meaningful and concise response.
            prompt = f"""
                Question: {text}
                Data: {relevant_data}
                Provide brief and impactful insights 
                that can be drawn from above question and data
            """

            # Generate the final response using the OpenAI model.
            response = self.llm.invoke(prompt)

            # Send the generated response and relevant data back to Slack.
            self.send_slack_response(body=body, msg=response, rel_data=relevant_data)
        except Exception as e:
            self.logger.info(f"Error occured at generating response --- {e}")

    def format_for_slack(self, text):

        """
            Converts markdown-like text into a Slack-compatible format.

            This function performs several transformations to make text compatible with Slack's formatting,
            such as converting bold, italics, headers, and lists into Slack's Markdown-like syntax.

            Arguments:
                text (str): The text that needs to be formatted for Slack.

            Returns:
                str: The formatted text, ready to be sent to Slack.
        """
        # Convert bold (**text**) to Slack-compatible (*text*)
        formatted_text = text.replace("**", "*")

        # Convert italics (__text__) to Slack-compatible (_text_)
        formatted_text = formatted_text.replace("__", "_")

        # Convert headers (### Header) to Slack-compatible (*Header*) for emphasis
        formatted_text = formatted_text.replace("### ", "*")

        # Format tables by replacing pipes and hyphens with plain text (Slack doesn't support tables directly)
        formatted_text = formatted_text.replace("|", "")
        formatted_text = formatted_text.replace(
            "---", "—"
        )  # Replace table dividers with em dashes

        # Convert ordered lists (1. item) and unordered lists (- item) to Slack-style lists
        lines = formatted_text.splitlines()
        for i, line in enumerate(lines):
            # Ordered list items
            if line.strip().startswith("1. "):
                lines[i] = line.replace("1. ", "• ", 1)  # Use bullet points instead

            # Unordered list items
            elif line.strip().startswith("- "):
                lines[i] = line.replace("- ", "• ", 1)

        # Join lines back together
        formatted_text = "\n".join(lines)

        # Optional: Replace multiple newlines with a single newline for cleaner formatting
        formatted_text = "\n".join(
            [line for line in formatted_text.splitlines() if line.strip()]
        )

        return formatted_text

    def send_slack_response(self, body, msg, rel_data):
        """
            Sends a response message to a Slack channel.

            This method constructs a Slack message with the relevant data and the
            GPT-generated response, then sends it to the appropriate Slack channel.

            Arguments:
                body (dict): The JSON payload from Slack, containing event details such as channel ID.
                msg (str): The response message generated by GPT, which will be sent to Slack.
                rel_data (str): The relevant data (e.g., a pivot table or processed dataset) to include in the message.

            Returns:
                None: Sends the message directly to the Slack channel.
        """
        try:
            # Step 1: Extract the Slack channel ID from the event body.
            channel_id = body["event"]["channel"]

            # Step 2: Prepare the headers for the Slack API request.
            headers = {
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json; charset=utf-8",
            }

            # Step 3: Construct the payload (message) to be sent to the Slack channel.
            # This includes:
            # - The channel ID (where the message will be sent)
            # - The relevant data (formatted as a code block)
            # - The GPT-generated message (formatted nicely for Slack)
            payload = {
                "channel": channel_id,
                "text": f"```\n{rel_data}\n```"
                + "\n"
                + self.format_for_slack(msg.content),
            }

            # Step 4: Send the request to Slack's API using the chat.postMessage endpoint.
            response = requests.post(self.slack_url, headers=headers, json=payload)
        except Exception as e:
            self.logger.info(f"Error occured at sending slack response --- {e}")

    def send_processing_message(self, body, msg="Working on your data request..."):
        """
            Sends a processing message to the Slack channel to notify users
            that their request is being worked on.

            This function sends a message to the specified Slack channel
            using the `chat.postMessage` API endpoint.

            Arguments:
                body (dict): The JSON payload from Slack containing event details.
                msg (str): The message to send to the Slack channel. Defaults to a standard processing message.

            Returns:
                None: Sends a message directly to the Slack channel.
        """
        try:
            channel_id = body["event"]["channel"]
            # url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json; charset=utf-8",
            }
            # Construct the payload with the channel ID and the message to be sent.
            payload = {
                "channel": channel_id,
                "text": msg,
            }
            response = requests.post(self.slack_url, headers=headers, json=payload)
        except Exception as e:
            self.logger.info(f"Error occured at sending slack response --- {e}")

    def load_data_from_s3(self):
        """
            Loads data from an S3 bucket into a pandas DataFrame.
            
            This method fetches a CSV file from a specified S3 bucket, reads its content,
            and loads it into a pandas DataFrame for further processing.
            
            Returns:
                None: The DataFrame is stored in the `self.learner_data` attribute.
        """
        # Define data types for specific columns to optimize memory usage and ensure data consistency.
        dtype = {
            "Learner ID": str,             # Learner ID as a string to preserve leading zeros
            "Course Prefix": str,          # Course prefix as string
            "Platform": str,               # Platform name as string
            "Course Name": str,            # Course name as string
            "Term": str,                   # Academic term as string
            "AY": str,                     # Academic Year as string
            "Verified": int,               # Binary indicator (0 or 1) for verification
            "Passed": int,                 # Binary indicator (0 or 1) for course completion
            "Credit Converted": int,       # Indicates if credit was converted (0 or 1)
            "Grade": int                   # Numerical grade
        }

        try:
            # Step 1: Fetch the CSV file from the S3 bucket.
            obj = self.s3.get_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_NAME)
            data = obj["Body"].read().decode("utf-8")

            # Step 2: Load the CSV data into a pandas DataFrame using the specified column types.
            self.learner_data = pd.read_csv(StringIO(data), dtype=dtype)
        except Exception as e:
            self.logger.info(f"Error at loading data from S3 --- {e}")

    def load_data_from_csv(self, file_path: str):
        """
            Loads data from a local CSV file into a pandas DataFrame.
            
            This method reads the content of a CSV file located on the local filesystem
            and stores it in the `self.learner_data` attribute for further processing.

            Arguments:
                file_path (str): The full path to the CSV file to be loaded.

            Returns:
                None: The loaded data is stored in the `self.learner_data` attribute.
        """
        dtype = {
            "Learner ID": str,             # Learner ID as a string to preserve leading zeros
            "Course Prefix": str,          # Course prefix as string
            "Platform": str,               # Platform name as string
            "Course Name": str,            # Course name as string
            "Term": str,                   # Academic term as string
            "AY": str,                     # Academic Year as string
            "Verified": int,               # Binary indicator (0 or 1) for verification
            "Passed": int,                 # Binary indicator (0 or 1) for course completion
            "Credit Converted": int,       # Indicates if credit was converted (0 or 1)
            "Grade": int                   # Numerical grade
        }

        try:
            # Read the CSV file using pandas and enforce the defined column data types
            self.learner_data = pd.read_csv(file_path, dtype=dtype)
            self.logger.info(f"Data successfully loaded from {file_path}.")
        except Exception as e:
            self.logger.error(f"Error loading data from CSV file --- {e}")

    def url_verification_handler(self, slack_event):
        """
            Handles Slack URL verification events.

            When a new Slack Event Subscription is created, Slack sends a verification request
            to your server with a challenge token. This method responds with the provided
            challenge token to confirm the URL is valid.

            Arguments:
                slack_event (dict): The JSON payload sent by Slack containing the challenge token.

            Returns:
                dict: A dictionary containing the HTTP status code and the challenge response.
        """
        # Extract the "challenge" parameter from the Slack event payload.
        challenge_answer = slack_event.get("challenge")

        # Log the verification event for debugging and auditing purposes.
        self.logger.info(f"url_verification_handler was called")
        return {"statusCode": 200, "body": challenge_answer}

    def log(self, txt):
        self.logger.info(f"{txt}")

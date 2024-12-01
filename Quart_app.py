"""
    This code defines a Slack AI Assistant using Quart Python Framework
    The purpose of this code is to receive and process Slack events, such as app mentions, perform some actions on the event received
    and provide the output as slack message in a communication channel.

    The code is structured to handle requests from Slack, verify incoming URLs, and respond to app mentions by delegating 
    heavy processing to a background task. 
"""

"""
    Required Libraries:
    
    logging - Provides a way to log messages, errors, and other information to the console or a file.
        Useful for debugging and tracking application behavior during runtime.

    dotenv - Loads environment variables from a `.env` file into the system environment.
        find_dotenv - Searches for the `.env` file in the current directory and its parent directories.
        load_dotenv - Loads the `.env` file and sets environment variables, making them accessible via `os.environ`.

    os - Provides a way to interact with the operating system, including accessing environment variables and file paths.

    quart - An asynchronous web framework .
        Quart is designed to work with Python's `asyncio` library, making it suitable for handling asynchronous tasks.
        Quart components:
            - Quart: The core web application class.
            - request: Handles incoming HTTP requests, allowing you to extract data from them.
            - jsonify: A utility to convert Python dictionaries into JSON responses.
    
    asyncio - Python's built-in library for writing concurrent code using async/await.
        Useful for running asynchronous tasks, such as processing Slack events without blocking the main event loop.

    slack_bot_handler - A custom module (defined separately) that contains logic to handle various Slack events and responses.
"""
import logging
from dotenv import find_dotenv, load_dotenv
import os
from quart import Quart, request, jsonify
from slack_bot_handler import SlackBotHandler
import asyncio



# Set up basic logging configuration for console output:
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO (can be adjusted to DEBUG, WARNING, etc.)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format includes timestamp, log level, and message
)
logger = (
    logging.getLogger()
)

# Initialize the Quart web application:
# - Quart is used to handle incoming HTTP requests from Slack.
# - This instance (`stark`) serves as the main web server for processing events and responding to Slack.
# - The instance name can be anything - here we used `stark`
stark = Quart(__name__)

# Create an instance of the SlackBotHandler class:
# - `SlackBotHandler` is a custom class defined in the `slack_bot_handler.py` module.
# - It contains logic to process various Slack events, like app mentions, messages, and responses.
# - This instance (`handler`) is used throughout the application to handle Slack interactions.
handler = SlackBotHandler()


async def handle_app_mention(slack_body):
    """
    Asynchronously handles app mentions from Slack.

    - This function offloads heavy processing to a background thread using `asyncio.to_thread`.
    - Slack needs a success message within 3 seconds, so this function will push event details 
    - to background task and we can send success message within 3 seconds to slack

    Args:
        slack_body (dict): The JSON payload received from Slack containing details of the event.
    """
    await asyncio.to_thread(handler.handle_app_mention, slack_body)


@stark.route("/slack/events", methods=["POST"])
async def slack_events():
    """
    Endpoint to handle incoming Slack events.

    This route listens for incoming POST requests from Slack's Events API. It handles:
    - `url_verification`: The initial handshake request from Slack to verify the endpoint.
    - `app_mention`: When the bot is mentioned in a Slack channel.

    Returns:
        - A 200 response if the request is successfully processed.
        - A 400 response if the request type is unrecognized or invalid.
    """
    logger.info("Slack request recieved.")

    # Parse the incoming JSON payload from the Slack request
    slack_body = await request.json

    # Handle Slack's URL verification challenge (initial handshake)
    if slack_body.get("type") == "url_verification":
        return handler.url_verification_handler(slack_body)

    # Check if the event is an 'app_mention' (triggered when the bot is mentioned)
    if slack_body.get("event", {}).get("type") == "app_mention":
        # Offload the processing of the mention event to a background task
        asyncio.create_task(handle_app_mention(slack_body))
        logging.info("Slack request completed.")
        return jsonify({"statusCode": 200})

    # If the event type is not recognized, return a 400 Bad Request response
    logging.info("Slack request invalid.")
    return jsonify({"statusCode": 400, "body": "Invalid request"})


@stark.route("/health", methods=["GET"])
async def health_endpoint():
    """
    Health check endpoint to confirm the server is running.

    Returns:
        - A JSON response with status 200 and a message indicating that the API is live.
    """
    return jsonify({"statusCode": 200, "message": "API is live."})



if __name__ == "__main__":
    """
        Entry point of the application.
        
        - Runs the Quart web server in debug mode on port 3081.
        - The debug mode provides more detailed error messages during development.
    """
    stark.run(debug=True, port=3081)

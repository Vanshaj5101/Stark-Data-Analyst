import requests
import os
from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv(), override=True)


# Replace 'your_bearer_token_here' with your actual Slack API token
bearer_token = os.environ["SLACK_BOT_TOKEN"]

# Define the headers for the request
headers = {"Authorization": f"Bearer {bearer_token}"}

# Make the GET request to the Slack API endpoint
response = requests.get("https://slack.com/api/auth.test", headers=headers)

# Print the response
if response.status_code == 200:
    print("Response:", response.json())
else:
    print("Failed to fetch data. Status Code:", response.status_code)
    print("Error:", response.text)

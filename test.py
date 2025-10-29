"""
Test script for OpenAI API connection and basic LLM interaction.

This file demonstrates how to:
- Load environment variables from .env file
- Initialize the OpenAI client
- Make a simple chat completion request
- Display the response

Note: This is a standalone test file not used in the main workflow.
"""

# Import required libraries
import os                          # For accessing environment variables
from openai import OpenAI          # OpenAI Python SDK for LLM interactions
from dotenv import load_dotenv     # For loading .env configuration file

# Load environment variables from .env file in project root
# This allows us to keep sensitive credentials (like API keys) out of the code
load_dotenv()

# Initialize the OpenAI client using the API key from environment variables
# The API key should be stored in a .env file as: OPENAI_API_KEY=your_key_here
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create a chat completion request to the LLM
# This is a simple test to verify the API connection works
response = client.chat.completions.create(
    model="gpt-5",  # Note: "gpt-5" may not be a valid model - typically use "gpt-4o", "gpt-4", "gpt-3.5-turbo", etc.
    messages=[
        {
            "role": "user", 
            "content": "Explain how LLMs work as if I'm a 5 year old"
        }
    ]
)

# Extract and print the AI's response content
print(response.choices[0].message.content)
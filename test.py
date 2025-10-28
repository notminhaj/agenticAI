import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Loads .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": "Explain how LLMs work as if I'm a 5 year old"}
    ]
)
print(response.choices[0].message.content)
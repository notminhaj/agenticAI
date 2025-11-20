# chatbot.py
import os
from datetime import datetime
from crewai import Agent, Task, Crew
from agents.tutor_agent import create_tutor_agent
from prompts import CHATBOT_EXPECTED_OUTPUT

# Create the persistent tutor
tutor = create_tutor_agent()

print("Your sarcastic AI tutor is online.")
print("Type 'quit' to exit. Type 'brief' for weekly summary.\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["quit", "exit", "bye"]:
        print("Tutor: Catch you later, genius.")
        break
    if user_input.lower() == "brief":
        user_input = "Generate my weekly AI brief based on my current knowledge gaps."

    task = Task(
        description=f"""The user just said: {user_input}
        Any piece of information you share must come from a source.
        Your response must be catered to the user's level of understanding
        Whenever you present the user with new information, update their knowledge base before presenting your final answer""",
        expected_output=CHATBOT_EXPECTED_OUTPUT,
        agent=tutor
    )

    crew = Crew(agents=[tutor], tasks=[task], verbose=1, tracing=True)
    response = crew.kickoff()

    print(f"\nTutor: {response}\n")
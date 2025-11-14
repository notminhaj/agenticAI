from crewai import Agent, Task, Crew, LLM
from tools import search, summarize, fetch, persist, rank_documents
from prompts import role, goal, backstory, description, expected_output
import os

llm = LLM(
    model="llama-3.2-90b-vision-preview",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

gpt = LLM(
    model = "gpt-4.1-mini"
)

agent = Agent(
    role=role,
    goal=goal,
    backstory=backstory,
    tools=[search, summarize, fetch, persist, rank_documents],
    verbose=True,
    llm=gpt
)

task = Task(
    description=description,
    expected_output=expected_output,
    agent=agent,
    verbose=True
)

crew = Crew(
    agents=[agent],
    tasks=[task],
    verbose=True
)

result = crew.kickoff()
print(result)

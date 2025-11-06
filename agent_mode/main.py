from crewai import Agent, Task, Crew
from tools import search, summarize, fetch, persist
from langchain_openai import ChatOpenAI

agent = Agent(
    role="A sarcastic researcher in the field of AI",
    goal="Create a weekly brief of the most recent AI papers in the field",
    backstory="You are a hilarious person",
    tools=[search, summarize, fetch, persist],
    verbose=True,
    LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0.7),
)

task = Task(
    description="Create a weekly brief of the 2 recent AI papers in the field",
    expected_output="Document and save a markdown formatted weekly brief of the 2 recent AI papers in the field",
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

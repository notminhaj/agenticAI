from crewai import Agent, Task, Crew
from tools import search, summarize, fetch, persist

agent = Agent(
    role="A sarcastic researcher in the field of AI",
    model = "gpt-4o-mini",
    goal="Create a weekly brief of the most important AI papers in the field",
    backstory="You are a hilarious person",
    tools=[search, summarize, fetch, persist],
    verbose=True
)

task = Task(
    description="Create a weekly brief of the 2 recent AI papers in the field",
    expected_output="Document and save a markdown formatted weekly brief of the recent AI papers in the field",
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

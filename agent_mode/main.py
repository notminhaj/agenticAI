from crewai import Agent, Task, Crew
from tools import search, summarize, fetch, persist

agent = Agent(
    role="A sarchastic researcher in the field of AI",
    goal="Create a weekly brief of the most important AI papers in the field",
    backstory="You are a paranoid person who always double check's everything",
    tools=[search, summarize, fetch, persist],
    verbose=True
)

task = Task(
    description="Create a weekly brief of the 3 most important AI papers in the field",
    expected_output="Document a markdown formatted weekly brief of the most important AI papers in the field",
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

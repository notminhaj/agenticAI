from crewai import Agent, Task, Crew, LLM
from tools import search, summarize, fetch, persist

agent = Agent(
    role="A sarcastic researcher in the field of AI",
    goal="Create a weekly brief of the most recent AI papers in the field",
    backstory="You are a hilarious person",
    tools=[search, summarize, fetch, persist],
    verbose=True,
    llm = LLM(model="gpt-5-nano")
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

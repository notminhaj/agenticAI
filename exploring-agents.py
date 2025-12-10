from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup

@tool
def get_weather(city: str) -> str:
    """Get real current weather for a city by scraping wttr.in."""
    try:
        # Fetch plain text weather from wttr.in (e.g., "curl wttr.in/London")
        url = f"https://wttr.in/{city}?format=3"  # Format=3: "City: condition, temp"
        response = requests.get(url, headers={'User-Agent': 'curl'})  # Mimic curl to avoid blocks
        
        if response.status_code == 200:
            return response.text.strip() + " "  # E.g., "San Francisco: ☀️ +62°F"
        else:
            return f"Weather not found for {city}. Try another spelling."
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

print(get_weather("San Francisco"))


model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.7)

prompt = PromptTemplate.from_template(
    """You are a funny weatherman. 
In a concise manner, describe it with personality: "super chilly", "toasty warm", "blazing hot", etc.

Available tools:
{tools}
Tool names: {tool_names}

Use this format:

Question: {input}
Thought: I should use a tool
Action: tool_name
Action Input: input_to_tool

Observation: the result
Thought: I now know the final answer
Final Answer: [Your fun, natural answer]

Begin!

Question: {input}
{agent_scratchpad}"""
)

agent = create_react_agent(
    llm=model,
    tools = [get_weather],
    prompt = prompt
)
executor = AgentExecutor(agent=agent, tools=[get_weather], verbose=True)

# === RUN ===
response = executor.invoke({
    "input": "What is the weather in Melbourne?"
})

print("\nFINAL ANSWER:")
print(response["output"])

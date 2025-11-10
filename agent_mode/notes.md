# Development Notes

## ISSUE: This agent sure loves to blast tokens: 0.02 cents everytime I run main.py
- When I check my logs, weirdly enough it sometimes uses GPT-4.1-mini even though I set the model to GPT-4o-mini
- No solution yet

## ISSUE: Agent is not using the persist() tool and as a result, output is structureless
- Changed expected output prompt from "A structured, markdown formatted weekly brief..."
- to "Document a markdown formatted weekly brief..."
- Prompt affects which tools LLMs decide to call 
- Because they are stochastic and every word has an attention value

## ISSUE: I set the agent role to be a sarchastic researcher, however no sarchasm is found in the report
- Where in the long chain of prompts is the agent shifting towards professionalism?
- Why is any other prompt able to override the system (role) prompt?

## Random decision the LLM makes on its own
- I set the search tool's topic to "Agentic AI" by default
- def search(topic: str = "Agentic AI", ...):
- But the Agent searches similar topics like "Deep Learning" and "machine learning" by itself

## NOTE
- CrewAI agents follow multiple chains of prompt
- That's why sarchasm was lost
- Integrated better prompt system (prompts.py)

## Issue: Why is there a topic drift? (AI -> Deep Learning)
- Due to old flawed prompt system the stochastic LLM only reseived "AI" as field
- Changes the variable to anything as AI can involve many things
- Updated prompt system fixes this.

## NOTE
- Setting model to gpt-5-nano it searched for 5 papers instead of 3
- More explorative?
- Thought said it will pick the best 3 papers to create a summary on
- Takes a LONG time compared to gpt-4.1-mini

## ISSUE: GPT 5 nano sometimes fails to use a tool correctly
- Model is small
- May fail to follow conventions / correct structure for tool usage.
- E.g. tried using persist with tool input "tokens_in", 1088,... (correct would be "tokens_in":1088,...)
- Loses sarchasm as well
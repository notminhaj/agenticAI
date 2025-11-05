# Development Notes

## ISSUE: Agent is not using the persist() tool and as a result, output is structureless
- Changed expected output prompt from "A structured, markdown formatted weekly brief..."
- to "Document a markdown formatted weekly brief..."
- Prompt affects which tools LLMs decide to call 
- Because they are stochastic and every word has an attention value

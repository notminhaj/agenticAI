import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from crewai.tools import tool

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

@tool
def summarize(raw_text: str, title_guess: str = "Untitled") -> dict:
    """
    Generate an AI-powered summary of an academic paper.
    
    Uses OpenAI's GPT-4.1-mini model to create a structured, concise summary.
    The summary follows a specific template with sections for Problem, Approach, Results, and Significance.
    
    Args:
        raw_text (str): Full text content of the paper to summarize.
        title_guess (str): Estimated or extracted title of the paper.
        
    Returns:
        dict: Summary result containing:
            - title (str): Paper title
            - summary (str): LLM-generated structured summary in markdown format
            - tokens_in (int): Number of input tokens used (for cost tracking)
            - tokens_out (int): Number of output tokens used (for cost tracking)
            
    Raises:
        ValueError: If OPENAI_API_KEY is not found in environment variables
        
    Note:
        The function truncates input text to 6000 characters to manage token costs.
        It automatically retries once on API failures before giving up.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or .env file")
    client = OpenAI(api_key=api_key)
    
    # Try to import prompts, but provide defaults if not available
    try:
        from prompts import role, goal, backstory, description
    except ImportError:
        # Default prompts if prompts module is not available
        role = "An expert researcher"
        goal = "Create clear, concise summaries"
        backstory = "You are an experienced academic researcher"
        description = "Summarize the provided content"
    
    prompt = (
        f"Your role is {role}" +
        f"Your goal is {goal}" +
        f"Your backstory is {backstory}" +
        f"Your task is {description}" +
        f"Use EXACTLY this structure with these exact headers:\n\n" +
        f"**Problem:** [description]\n" +
        f"**Approach:** [description]\n" +
        f"**Key Results:** [description]\n" +
        f"**Why It Matters:** [description]\n\n" +
        f"Keep each section to 30-50 words. Total 120180 words.\n\n" +
        f"Title: {title_guess}\n\n{raw_text[:6000]}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        summary = response.choices[0].message.content.strip()
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens
        return {"title": title_guess, "summary": summary, "tokens_in": tokens_in, "tokens_out": tokens_out}
    except Exception as e:
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            summary = response.choices[0].message.content.strip()
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
            return {"title": title_guess, "summary": summary, "tokens_in": tokens_in, "tokens_out": tokens_out}
        except:
            return {"title": title_guess, "summary": "Error summarizing: " + str(e), "tokens_in": 0, "tokens_out": 0}


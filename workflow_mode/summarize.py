"""
LLM-based summarization module.

This module uses OpenAI's GPT models to generate structured summaries of academic papers.
Summaries are formatted for busy practitioners who need quick insights.

Features:
- Structured output (Problem, Approach, Results, Why It Matters)
- Token usage tracking for cost monitoring
- Automatic retry on API failures
- Content truncation for token efficiency
"""

# Import required libraries
from openai import OpenAI      # OpenAI Python SDK for LLM API calls
import os                       # Environment variable access
from pathlib import Path        # Path manipulation
from dotenv import load_dotenv  # Load .env file for configuration

# Load environment variables from .env file in project root
# The .env file should contain: OPENAI_API_KEY=your_api_key_here
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def summarize(raw_text: str, title_guess: str = "Untitled") -> dict:
    """
    Generate an AI-powered summary of an academic paper.
    
    Uses OpenAI's GPT-4o-mini model to create a structured, concise summary
    formatted for busy AI practitioners. The summary follows a specific template
    with sections for Problem, Approach, Results, and Significance.
    
    Args:
        raw_text (str): Full text content of the paper to summarize
        title_guess (str): Estimated or extracted title of the paper. Default: "Untitled"
        
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
    # ================================================
    # Setup: Load API key and initialize client
    # ================================================
    
    # Retrieve API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Validate that API key exists
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or .env file")
    
    # Initialize OpenAI client with the API key
    client = OpenAI(api_key=api_key)
    
    # ================================================
    # Build the summarization prompt
    # ================================================
    
    # Construct a detailed prompt that instructs the LLM on:
    # - Target audience (busy Junior AI Intern)
    # - Required structure (specific headers)
    # - Format requirements (markdown with bold headers)
    # - Length constraints (30-50 words per section, 120-180 total)
    prompt = (
        f"Summarize the following AI paper for a busy Junior AI Intern. "
        f"Use EXACTLY this structure with these exact headers:\n\n"
        f"**Problem:** [description]\n"        # What problem does the paper address?
        f"**Approach:** [description]\n"        # How did they solve it?
        f"**Key Results:** [description]\n"     # What did they find?
        f"**Why It Matters:** [description]\n\n"  # Why is this important?
        f"Keep each section to 30-50 words. Total 120–180 words.\n\n"
        f"Title: {title_guess}\n\n{raw_text[:6000]}"  # Truncate to 6000 chars for token efficiency
    )

    # ================================================
    # Attempt 1: Primary API call
    # ================================================
    try:
        # Make API request to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",              # Fast and cost-effective model
            messages=[{"role": "user", "content": prompt}],  # Single user message
            temperature=0.7,                  # Balance between creativity and consistency
            max_tokens=300                    # Limit output length to control costs
        )
        
        # Extract the summary text from the response
        summary = response.choices[0].message.content.strip()
        
        # Extract token usage for cost tracking and monitoring
        tokens_in = response.usage.prompt_tokens   # Tokens in the prompt (input)
        tokens_out = response.usage.completion_tokens  # Tokens in the completion (output)
        
        # Return the result dictionary
        return {
            "title": title_guess,
            "summary": summary,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out
        }
        
    except Exception as e:
        # ================================================
        # Attempt 2: Retry on failure
        # ================================================
        # Network issues and rate limits are common - retry once before giving up
        try:
            # Make the same request again
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            # Extract results
            summary = response.choices[0].message.content.strip()
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
            
            # Return successful result
            return {
                "title": title_guess,
                "summary": summary,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out
            }
        except:
            # ================================================
            # Final fallback: Return error message
            # ================================================
            # Both attempts failed - return an error result rather than crashing
            return {
                "title": title_guess,
                "summary": "Error summarizing: " + str(e),
                "tokens_in": 0,
                "tokens_out": 0
            }
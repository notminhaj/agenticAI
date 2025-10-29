# summarize.py
from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from parent directory (project root)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def summarize(raw_text: str, title_guess: str = "Untitled") -> dict:
    """
    Summarize AI paper text with LLM.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or .env file")
    
    client = OpenAI(api_key=api_key)
    
    prompt = (
        f"Summarize the following AI paper for a busy Junior AI Intern. "
        f"Use EXACTLY this structure with these exact headers:\n\n"
        f"**Problem:** [description]\n"
        f"**Approach:** [description]\n"
        f"**Key Results:** [description]\n"
        f"**Why It Matters:** [description]\n\n"
        f"Keep each section to 30-50 words. Total 120–180 words.\n\n"
        f"Title: {title_guess}\n\n{raw_text[:6000]}"  # Truncate to 6000 chars
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        
        summary = response.choices[0].message.content.strip()
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens
        
        return {
            "title": title_guess,
            "summary": summary,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out
        }
    except Exception as e:
        # Retry once with same prompt
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
            )
            summary = response.choices[0].message.content.strip()
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
            
            return {
                "title": title_guess,
                "summary": summary,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out
            }
        except:
            return {
                "title": title_guess,
                "summary": "Error summarizing: " + str(e),
                "tokens_in": 0,
                "tokens_out": 0
            }
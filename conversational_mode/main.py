"""
Conversational Mode - Main Entry Point

This is the entry point for the conversational AI tutor.
Run with: python conversational_mode/main.py

TESTING MODE:
- Set TESTING=True in config.py for verbose debug output
- Set TESTING=False for production (clean output)
"""

import os
import sys

# Ensure conversational_mode is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from tutor_agent import create_tutor
from config import TESTING


def main():
    """Main entry point for the conversational tutor."""
    if TESTING:
        print("=" * 60)
        print("CONVERSATIONAL AI TUTOR - DEBUG MODE")
        print("=" * 60)
    else:
        print("Conversational AI Tutor")
        print("-" * 40)
    
    try:
        agent = create_tutor()
        
        print("\nTutor: Hello! I'm your AI Tutor. I've loaded your knowledge base")
        print("       and I'm ready to help you learn. What would you like to explore?")
        print("\n       (Type 'exit', 'quit', or 'bye' to end the session)")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nTutor: Goodbye! Keep learning! 🎓")
                    break
                
                response = agent.chat(user_input)
                print(f"\nTutor: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nTutor: Goodbye! Keep learning! 🎓")
                break
            except Exception as e:
                if TESTING:
                    print(f"\n[ERROR] Exception in chat: {e}")
                    import traceback
                    traceback.print_exc()
                else:
                    print("\nTutor: I encountered an issue. Let me try again.")
                    
    except Exception as e:
        print(f"Failed to initialize tutor: {e}")
        if TESTING:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

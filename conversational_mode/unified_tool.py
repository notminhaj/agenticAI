import sys
import io
import contextlib
import traceback
import os
from typing import Any, Dict

# Ensure the parent directory is in path so we can import 'tools'
# Assuming this file is in conversational_mode/unified_tool.py
# and tools is in conversational_mode/tools
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def execute_tool(code: str) -> Dict[str, Any]:
    """
    Executes the given Python code in a sandbox environment.
    The code can import tools from the 'tools' package.
    Returns a dictionary with 'stdout' and 'result'.
    
    The code should assign the final return value to a variable named 'result' 
    if it wants to return something specific. 
    Otherwise, the function returns None for 'result'.
    """
    # Capture stdout
    stdout_buffer = io.StringIO()
    
    # Global context for execution
    global_context = {}
    
    try:
        with contextlib.redirect_stdout(stdout_buffer):
            # Execute the code
            exec(code, global_context)
            
        # Retrieve 'result' from the context if it exists
        result = global_context.get('result', None)
        stdout = stdout_buffer.getvalue()
        
        return {
            "stdout": stdout,
            "result": result
        }
        
    except Exception:
        # Return error information
        return {
            "stdout": stdout_buffer.getvalue(),
            "error": traceback.format_exc()
        }

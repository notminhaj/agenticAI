"""
Mode Router.

Responsible for loading the correct adapter based on ACTIVE_MODE
configuration and routing requests to it.
"""

from typing import Optional
from .config import config
from .adapters import (
    BaseAdapter,
    ConversationalAdapter,
    WorkflowAdapter,
    AgentAdapter,
)


# Registry of available adapters
ADAPTER_REGISTRY = {
    "conversational_mode": ConversationalAdapter,
    "workflow_mode": WorkflowAdapter,
    "agent_mode": AgentAdapter,
}

# Singleton adapter instance
_adapter_instance: Optional[BaseAdapter] = None


def get_adapter() -> BaseAdapter:
    """
    Get the active mode adapter.
    
    Returns a singleton instance of the adapter configured
    by ACTIVE_MODE environment variable.
    
    Returns:
        BaseAdapter instance for the active mode
        
    Raises:
        ValueError: If ACTIVE_MODE is not a valid mode name
    """
    global _adapter_instance
    
    if _adapter_instance is None:
        mode = config.ACTIVE_MODE
        
        if mode not in ADAPTER_REGISTRY:
            valid_modes = ", ".join(ADAPTER_REGISTRY.keys())
            raise ValueError(
                f"Unknown mode: '{mode}'. "
                f"Valid modes are: {valid_modes}"
            )
        
        adapter_class = ADAPTER_REGISTRY[mode]
        _adapter_instance = adapter_class()
        
        if config.DEBUG:
            print(f"[Router] Initialized adapter: {mode}")
    
    return _adapter_instance


def get_available_modes() -> list:
    """Return list of available mode names."""
    return list(ADAPTER_REGISTRY.keys())


def get_active_mode() -> str:
    """Return the currently active mode name."""
    return config.ACTIVE_MODE

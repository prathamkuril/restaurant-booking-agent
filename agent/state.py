"""
Conversation State Management.

Defines the state schema for the restaurant booking conversation
and manages context across multiple turns.
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    """State schema for restaurant booking conversations."""
    
    # Conversation history
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Current booking context
    current_booking_reference: Optional[str]
    
    # Parsed user intent and entities
    intent: Optional[str]
    entities: Dict[str, Any]
    
    # API response cache
    last_api_response: Optional[Dict[str, Any]]
    
    # Session information
    session_id: str
    user_name: Optional[str]
    
    # Booking details being collected
    pending_booking: Dict[str, Any]
    
    # Error state
    error: Optional[str]


def initialize_state(session_id: str) -> ConversationState:
    """
    Initialize a new conversation state.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Initialized conversation state
    """
    return {
        "messages": [],
        "current_booking_reference": None,
        "intent": None,
        "entities": {},
        "last_api_response": None,
        "session_id": session_id,
        "user_name": None,
        "pending_booking": {},
        "error": None
    }
"""
LangGraph Restaurant Booking Agent.

Implements the conversation flow using LangGraph for state management
and tool orchestration.
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import logging
import re
from datetime import datetime

from agent.state import ConversationState, initialize_state
from agent.llm_client import LlamaClient
from agent.api_client import BookingAPIClient
from agent.tools import BookingTools
from agent.prompts import (
    SYSTEM_PROMPT, 
    INTENT_EXTRACTION_PROMPT,
    ERROR_MESSAGES,
    CONFIRMATION_TEMPLATES,
    format_availability_slots
)

logger = logging.getLogger(__name__)


class RestaurantBookingAgent:
    """Main agent for handling restaurant bookings."""
    
    def __init__(self):
        """Initialize the booking agent."""
        self.llm_client = LlamaClient()
        self.api_client = BookingAPIClient()
        self.tools = BookingTools(self.api_client)
        self.graph = self._build_graph()
        logger.info("Restaurant booking agent initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph.
        
        Returns:
            Configured state graph
        """
        # Create graph with state schema
        graph = StateGraph(ConversationState)
        
        # Add nodes
        graph.add_node("process_input", self.process_input)
        graph.add_node("check_availability", self.check_availability_node)
        graph.add_node("create_booking", self.create_booking_node)
        graph.add_node("get_booking", self.get_booking_node)
        graph.add_node("update_booking", self.update_booking_node)
        graph.add_node("cancel_booking", self.cancel_booking_node)
        graph.add_node("handle_conversation", self.handle_conversation_node)
        graph.add_node("respond", self.respond_node)
        
        # Set entry point
        graph.set_entry_point("process_input")
        
        # Add conditional edges based on intent
        graph.add_conditional_edges(
            "process_input",
            self.route_intent,
            {
                "check_availability": "check_availability",
                "create_booking": "create_booking",
                "get_booking": "get_booking",
                "update_booking": "update_booking",
                "cancel_booking": "cancel_booking",
                "conversation": "handle_conversation",
                "respond": "respond"
            }
        )
        
        # All action nodes lead to respond
        for node in ["check_availability", "create_booking", "get_booking", 
                    "update_booking", "cancel_booking", "handle_conversation"]:
            graph.add_edge(node, "respond")
        
        # Respond leads to END
        graph.add_edge("respond", END)
        
        return graph.compile()
    
    async def process_input(self, state: ConversationState) -> ConversationState:
        """
        Process user input and extract intent.
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with intent and entities
        """
        try:
            # Get last user message
            if not state["messages"]:
                return state
            
            last_message = state["messages"][-1]
            if not isinstance(last_message, HumanMessage):
                return state
            
            user_text = last_message.content
            
            # Extract intent and entities
            prompt = INTENT_EXTRACTION_PROMPT.format(user_message=user_text)
            extraction_result = await self.llm_client.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            
            # Parse extraction result
            intent, entities = self._parse_extraction(extraction_result)
            
            state["intent"] = intent
            state["entities"] = entities
            
            logger.info(f"Processed input - Intent: {intent}, Entities: {entities}")
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    def route_intent(self, state: ConversationState) -> str:
        """
        Route to appropriate node based on intent.
        
        Args:
            state: Current conversation state
            
        Returns:
            Next node name
        """
        intent = state.get("intent")
        
        if not intent:
            return "respond"
        
        # Check if we have required entities for each intent
        entities = state.get("entities", {})
        
        if intent == "check_availability":
            if entities.get("date") and entities.get("party_size"):
                return "check_availability"
            return "conversation"  # Need more info
        
        elif intent == "create_booking":
            # Check if we have minimum required info
            if entities.get("date") and entities.get("time") and entities.get("party_size"):
                return "create_booking"
            # If we have some info, collect the rest
            if entities.get("date") or entities.get("party_size"):
                state["pending_booking"].update(entities)
            return "conversation"
        
        elif intent == "get_booking":
            if entities.get("booking_reference") or state.get("current_booking_reference"):
                return "get_booking"
            return "conversation"
        
        elif intent == "update_booking":
            if entities.get("booking_reference") or state.get("current_booking_reference"):
                return "update_booking"
            return "conversation"
        
        elif intent == "cancel_booking":
            if entities.get("booking_reference") or state.get("current_booking_reference"):
                return "cancel_booking"
            return "conversation"
        
        else:
            return "conversation"
    
    async def check_availability_node(self, state: ConversationState) -> ConversationState:
        """Check availability and update state."""
        try:
            entities = state.get("entities", {})
            result = await self.tools.check_availability(
                date_str=entities.get("date"),
                party_size=int(entities.get("party_size"))
            )
            
            state["last_api_response"] = result
            
            if result["success"]:
                # Format response message
                message = CONFIRMATION_TEMPLATES["availability_results"].format(
                    date=result["date"],
                    party_size=result["party_size"],
                    available_slots=result["formatted_slots"]
                )
                state["messages"].append(AIMessage(content=message))
            else:
                state["error"] = result.get("error", "Failed to check availability")
        
        except Exception as e:
            logger.error(f"Error in check_availability_node: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def create_booking_node(self, state: ConversationState) -> ConversationState:
        """Create a booking and update state."""
        try:
            entities = state.get("entities", {})
            
            # Prepare customer info
            customer_info = {}
            if entities.get("customer_name"):
                parts = entities["customer_name"].split()
                customer_info["FirstName"] = parts[0] if parts else ""
                customer_info["Surname"] = " ".join(parts[1:]) if len(parts) > 1 else ""
            if entities.get("customer_email"):
                customer_info["Email"] = entities["customer_email"]
            if entities.get("customer_phone"):
                customer_info["Mobile"] = entities["customer_phone"]
            
            result = await self.tools.create_booking(
                date_str=entities.get("date"),
                time_str=entities.get("time"),
                party_size=int(entities.get("party_size")),
                customer_info=customer_info if customer_info else None,
                special_requests=entities.get("special_requests")
            )
            
            state["last_api_response"] = result
            
            if result["success"]:
                state["current_booking_reference"] = result["booking_reference"]
                
                # Format confirmation message
                booking = result["booking_details"]
                people = "person" if booking.get("party_size") == 1 else "people"
                special_req = ""
                if booking.get("special_requests"):
                    special_req = f"\n💬 Special requests: {booking['special_requests']}"
                
                message = CONFIRMATION_TEMPLATES["booking_created"].format(
                    date=booking.get("visit_date"),
                    time=booking.get("visit_time"),
                    party_size=booking.get("party_size"),
                    people=people,
                    reference=result["booking_reference"],
                    special_requests=special_req
                )
                state["messages"].append(AIMessage(content=message))
            else:
                state["error"] = result.get("error", "Failed to create booking")
        
        except Exception as e:
            logger.error(f"Error in create_booking_node: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def get_booking_node(self, state: ConversationState) -> ConversationState:
        """Get booking details and update state."""
        try:
            entities = state.get("entities", {})
            booking_ref = entities.get("booking_reference") or state.get("current_booking_reference")
            
            if not booking_ref:
                state["error"] = "No booking reference provided"
                return state
            
            result = await self.tools.get_booking(booking_ref)
            
            state["last_api_response"] = result
            
            if result["success"]:
                message = f"Here are your booking details:\n\n{result['formatted_details']}"
                state["messages"].append(AIMessage(content=message))
            else:
                state["error"] = result.get("message", "Booking not found")
        
        except Exception as e:
            logger.error(f"Error in get_booking_node: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def update_booking_node(self, state: ConversationState) -> ConversationState:
        """Update a booking and update state."""
        try:
            entities = state.get("entities", {})
            booking_ref = entities.get("booking_reference") or state.get("current_booking_reference")
            
            if not booking_ref:
                state["error"] = "No booking reference provided"
                return state
            
            result = await self.tools.update_booking(
                booking_reference=booking_ref,
                date_str=entities.get("date"),
                time_str=entities.get("time"),
                party_size=entities.get("party_size"),
                special_requests=entities.get("special_requests")
            )
            
            state["last_api_response"] = result
            
            if result["success"]:
                updates_text = "\n".join([f"• {k}: {v}" for k, v in result.get("updates", {}).items()])
                message = CONFIRMATION_TEMPLATES["booking_updated"].format(
                    reference=booking_ref,
                    updates=updates_text
                )
                state["messages"].append(AIMessage(content=message))
            else:
                state["error"] = result.get("error", "Failed to update booking")
        
        except Exception as e:
            logger.error(f"Error in update_booking_node: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def cancel_booking_node(self, state: ConversationState) -> ConversationState:
        """Cancel a booking and update state."""
        try:
            entities = state.get("entities", {})
            booking_ref = entities.get("booking_reference") or state.get("current_booking_reference")
            
            if not booking_ref:
                state["error"] = "No booking reference provided"
                return state
            
            result = await self.tools.cancel_booking(booking_ref)
            
            state["last_api_response"] = result
            
            if result["success"]:
                message = CONFIRMATION_TEMPLATES["booking_cancelled"].format(
                    reference=booking_ref
                )
                state["messages"].append(AIMessage(content=message))
                state["current_booking_reference"] = None  # Clear reference after cancellation
            else:
                state["error"] = result.get("error", "Failed to cancel booking")
        
        except Exception as e:
            logger.error(f"Error in cancel_booking_node: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def handle_conversation_node(self, state: ConversationState) -> ConversationState:
        """Handle general conversation and collect missing information."""
        try:
            # Build conversation context
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            messages.extend(state["messages"])
            
            # Add context about pending booking if any
            if state.get("pending_booking"):
                context = f"\nPending booking details collected so far: {state['pending_booking']}"
                messages.append(SystemMessage(content=context))
            
            # Generate response
            response = await self.llm_client.ainvoke(messages)
            state["messages"].append(AIMessage(content=response))
        
        except Exception as e:
            logger.error(f"Error in handle_conversation_node: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    async def respond_node(self, state: ConversationState) -> ConversationState:
        """Generate final response if not already added."""
        try:
            # Check if we have an error to handle
            if state.get("error"):
                error_msg = f"I apologize, but I encountered an issue: {state['error']}. Please try again or let me know how I can help."
                state["messages"].append(AIMessage(content=error_msg))
                state["error"] = None  # Clear error after handling
            
            # If last message is not an AI message, generate one
            elif not state["messages"] or not isinstance(state["messages"][-1], AIMessage):
                messages = [SystemMessage(content=SYSTEM_PROMPT)]
                messages.extend(state["messages"])
                response = await self.llm_client.ainvoke(messages)
                state["messages"].append(AIMessage(content=response))
        
        except Exception as e:
            logger.error(f"Error in respond_node: {str(e)}")
            fallback_msg = "I apologize, but I'm having trouble processing your request. Please try again."
            state["messages"].append(AIMessage(content=fallback_msg))
        
        return state
    
    def _parse_extraction(self, extraction_text: str) -> tuple:
        """
        Parse the extraction result from LLM.
        
        Args:
            extraction_text: Raw extraction text from LLM
            
        Returns:
            Tuple of (intent, entities)
        """
        try:
            lines = extraction_text.strip().split('\n')
            intent = None
            entities = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Intent:'):
                    intent = line.replace('Intent:', '').strip().lower()
                elif line.startswith('- '):
                    # Parse entity line
                    parts = line[2:].split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        entities[key] = value
            
            return intent, entities
        
        except Exception as e:
            logger.error(f"Error parsing extraction: {str(e)}")
            return None, {}
    
    async def process_message(
        self, 
        message: str, 
        session_id: str,
        state: Optional[ConversationState] = None
    ) -> ConversationState:
        """
        Process a user message through the graph.
        
        Args:
            message: User message
            session_id: Session ID
            state: Existing state or None for new conversation
            
        Returns:
            Updated conversation state
        """
        try:
            # Initialize or use existing state
            if state is None:
                state = initialize_state(session_id)
            
            # Add user message
            state["messages"].append(HumanMessage(content=message))
            
            # Run through graph
            result = await self.graph.ainvoke(state)
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            if state is None:
                state = initialize_state(session_id)
            state["messages"].append(HumanMessage(content=message))
            state["messages"].append(AIMessage(
                content="I apologize, but I'm having trouble processing your request. Please try again."
            ))
            return state
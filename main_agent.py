"""
Main FastAPI Application for Restaurant Booking Agent.

Provides both API endpoints and web interface for the booking agent.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import logging
import json
from pathlib import Path

from agent.agent_graph import RestaurantBookingAgent
from agent.state import ConversationState, initialize_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Restaurant Booking Agent",
    description="AI-powered restaurant booking assistant for TheHungryUnicorn",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = RestaurantBookingAgent()

# Store active sessions
sessions: Dict[str, ConversationState] = {}


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat interface."""
    return FileResponse("static/index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Process a chat message via REST API.
    
    Args:
        message: Chat message with optional session ID
        
    Returns:
        Agent response and session ID
    """
    try:
        # Get or create session
        session_id = message.session_id or str(uuid.uuid4())
        state = sessions.get(session_id)
        
        # Process message
        result_state = await agent.process_message(
            message.message,
            session_id,
            state
        )
        
        # Store updated state
        sessions[session_id] = result_state
        
        # Get last AI message
        ai_messages = [msg for msg in result_state["messages"] 
                      if hasattr(msg, '__class__') and 
                      msg.__class__.__name__ == 'AIMessage']
        
        response_text = ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't process that."
        
        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat.
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID for the conversation
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    try:
        # Get or create session state
        state = sessions.get(session_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": "Connected to restaurant booking assistant. How can I help you today?"
        })
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            if not user_message:
                continue
            
            logger.info(f"Received message from {session_id}: {user_message}")
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "content": "Agent is typing..."
            })
            
            try:
                # Process message
                result_state = await agent.process_message(
                    user_message,
                    session_id,
                    state
                )
                
                # Store updated state
                sessions[session_id] = result_state
                state = result_state
                
                # Get last AI message
                ai_messages = [msg for msg in result_state["messages"] 
                             if hasattr(msg, '__class__') and 
                             msg.__class__.__name__ == 'AIMessage']
                
                response_text = ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't process that."
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    "content": response_text
                })
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "content": "I encountered an error processing your message. Please try again."
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Clean up session after disconnect (optional)
        pass


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "restaurant-booking-agent"}


@app.get("/api/sessions")
async def get_sessions():
    """Get active session count (for monitoring)."""
    return {"active_sessions": len(sessions)}


@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a specific session.
    
    Args:
        session_id: Session ID to clear
        
    Returns:
        Confirmation message
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    
    # Ensure static directory exists
    Path("static").mkdir(exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main_agent:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
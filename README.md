# Restaurant Booking Conversational Agent

An intelligent, production-ready conversational agent for restaurant bookings, built with Llama3, LangGraph, and FastAPI. This system demonstrates advanced AI orchestration, state management, and real-world API integration.

## Overview

This project implements a sophisticated restaurant booking assistant that handles natural language conversations to:
- Check restaurant availability
- Create new bookings
- Retrieve booking details
- Modify existing reservations
- Cancel bookings

The agent features a modern web interface with real-time WebSocket communication and maintains conversation context across multiple turns.

## Architecture

### Technology Stack
- **LLM**: Llama3 8B (via Ollama) - Locally hosted for privacy and control
- **Agent Framework**: LangGraph - For complex conversation flow management
- **Web Framework**: FastAPI - High-performance async Python framework
- **Chat Interface**: HTML5/WebSocket - Real-time bidirectional communication
- **API Client**: httpx - Async HTTP client with robust error handling
- **State Management**: In-memory session store with LangGraph state schema

### System Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Web Interface     │────▶│   FastAPI Server    │
│  (HTML/WebSocket)   │◀────│    (Port 8000)      │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │   LangGraph Agent   │
                            │  (State Machine)    │
                            └──────────┬──────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                │                      │                      │
     ┌──────────▼──────────┐ ┌────────▼────────┐  ┌─────────▼─────────┐
     │   Llama3 Model      │ │  Booking Tools  │  │   API Client      │
     │   (via Ollama)      │ │  (Date Parser)  │  │  (Bearer Auth)    │
     └─────────────────────┘ └─────────────────┘  └─────────┬─────────┘
                                                             │
                                                  ┌──────────▼──────────┐
                                                  │  Restaurant API     │
                                                  │   (Port 8547)       │
                                                  └─────────────────────┘
```

## Getting Started

### Prerequisites
- Python 3.10+ (tested with 3.13)
- Ollama installed and running
- 8GB+ RAM for Llama3 model
- Unix-based OS (macOS/Linux) or WSL on Windows

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/prathamkuril/restaurant-booking-agent.git
cd restaurant-booking-agent
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download Llama3 model**
```bash
ollama pull llama3
```

5. **Start the mock API server**
```bash
python -m app
# Server runs on http://localhost:8547
```

6. **Start the agent server** (in a new terminal)
```bash
source venv/bin/activate
python main_agent.py
# Agent runs on http://localhost:8000
```

7. **Access the web interface**
```
Open browser to http://localhost:8000
```

## Features

### Core Capabilities

#### 1. Natural Language Understanding
- Intent recognition (booking, checking, modifying, cancelling)
- Entity extraction (dates, times, party sizes, references)
- Context retention across conversations
- Handling of relative dates ("tomorrow", "next Friday", "this weekend")

#### 2. Booking Operations
- **Check Availability**: Query available slots for specific dates
- **Create Booking**: Make reservations with customer details
- **View Booking**: Retrieve booking information by reference
- **Modify Booking**: Update date, time, or party size
- **Cancel Booking**: Remove reservations with reason tracking

#### 3. User Experience
- Real-time WebSocket communication
- Typing indicators for better UX
- Quick action buttons for common tasks
- Session persistence across page refreshes
- Error recovery and graceful fallbacks

### Advanced Features

#### State Management
- Conversation history tracking
- Pending booking collection
- Current booking reference retention
- Error state handling
- Session-based isolation

#### Date/Time Intelligence
- Natural language date parsing ("next Friday", "tomorrow")
- Business hours validation
- Future date enforcement
- Time format normalization

#### API Integration
- Bearer token authentication
- Request/response validation
- Error handling and retry logic
- Response caching for efficiency

## Design Rationale

### Why Llama3 + Ollama?
- **Privacy**: All processing happens locally, no data sent to external APIs
- **Cost**: No per-token charges, unlimited usage
- **Control**: Full control over model behavior and updates
- **Performance**: Sub-second response times with proper hardware

### Why LangGraph?
- **State Management**: Built-in conversation state handling
- **Flow Control**: Declarative conversation flow definition
- **Tool Integration**: Seamless integration with external tools
- **Scalability**: Graph-based architecture scales with complexity

### Why FastAPI?
- **Performance**: Built on Starlette and Pydantic for speed
- **WebSockets**: Native WebSocket support for real-time chat
- **Documentation**: Automatic API documentation generation
- **Type Safety**: Full type hints and validation

### Trade-offs Considered

1. **Local vs Cloud LLM**
   - Chose local for privacy and cost, accepting hardware requirements
   - Cloud would offer easier scaling but higher costs

2. **WebSocket vs REST**
   - WebSocket for real-time feel and persistent connections
   - REST API also available for simpler integrations

3. **In-Memory vs Database State**
   - In-memory for simplicity and speed in demo
   - Production would use Redis or database for persistence

### Monitoring & Observability

1. **Metrics**
   - Response time percentiles
   - Token usage and costs
   - API success/failure rates
   - Session duration and counts

2. **Logging**
   - Structured logging with correlation IDs
   - Conversation transcripts for quality review
   - Error tracking with stack traces

3. **Alerting**
   - High error rate alerts
   - Model response time degradation
   - Memory/CPU usage thresholds

## Limitations & Improvements

### Current Limitations
1. In-memory state lost on restart
2. Single restaurant support only
3. No user authentication
4. Limited to English language
5. No booking confirmation emails

### Potential Improvements
1. **Multi-restaurant Support**: Extend to handle multiple venues
2. **Persistent Storage**: Add database for state persistence
3. **Email Integration**: Send booking confirmations
4. **Multi-language**: Add translation layer
5. **Voice Interface**: Integrate speech-to-text/text-to-speech
6. **Analytics Dashboard**: Track booking patterns and user behavior
7. **A/B Testing**: Experiment with different conversation flows
8. **Feedback Loop**: Collect user satisfaction ratings

## API Documentation

### REST Endpoints

#### POST /api/chat
Process a chat message
```json
Request:
{
  "message": "I'd like to book a table for 4",
  "session_id": "optional-session-id"
}

Response:
{
  "response": "I'd be happy to help...",
  "session_id": "generated-or-provided-id"
}
```

#### WebSocket /ws/{session_id}
Real-time chat connection
```javascript
// Send message
ws.send(JSON.stringify({
  message: "Show availability for tomorrow"
}))

// Receive response
{
  type: "response",
  content: "Here are the available times..."
}
```



## Demo Scenarios

### Scenario 1: Complete Booking Flow
```
User: "Hi, I'd like to make a reservation"
Agent: "I'd be happy to help you make a reservation..."
User: "Show me what's available this Saturday"
Agent: "Here are the available times for Saturday..."
User: "Book 7pm for 4 people"
Agent: "Great! I've successfully made your booking..."
```

### Scenario 2: Modification Flow
```
User: "I have booking ABC1234"
Agent: "Let me check your booking details..."
User: "Change it to 8pm instead"
Agent: "Your booking has been successfully updated..."
```

## License

MIT License - See LICENSE file for details


## Contact

For questions or support, please open an issue on GitHub.

---

Built with passion for the Forward Deployed Engineer position at Appella AI
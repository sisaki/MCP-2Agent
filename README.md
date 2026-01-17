# MCP Agentic System (Planner–Executor)

This repo implements a simplified MCP-based agent architecture with:
- Planner LLM with conversation context
- Intent detection (search, summarize, conversation_query)
- Persistent CSV memory
- Confidence tracking
- Web UI with conversation history sidebar

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. API Keys are configured in `.env` file:
   - `SERPER_API_KEY` - For search functionality
   - `OPENAI_API_KEY` - For LLM operations (intent detection, planning, summarization) using GPT-4.1-nano
   
   The `.env` file is automatically loaded by all servers and the orchestrator.
   If you need to change the keys, edit the `.env` file directly.

## Run MCP Servers

### Option 1: Start Both Servers (One Command)
```bash
cd "/Users/anupam.purwar/Desktop/mcp-2agent" && /Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -m uvicorn servers:search_app --port 8001 --host 0.0.0.0 & /Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -m uvicorn servers:summary_app --port 8002 --host 0.0.0.0 &
```

### Option 2: Start Servers Separately
Open two terminal windows and run:

**Terminal 1 (Search Server):**
```bash
cd "/Users/anupam.purwar/Desktop/mcp-2agent"
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -m uvicorn servers:search_app --port 8001 --host 0.0.0.0
```

**Terminal 2 (Summary Server):**
```bash
cd "/Users/anupam.purwar/Desktop/mcp-2agent"
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -m uvicorn servers:summary_app --port 8002 --host 0.0.0.0
```

**Note**: If you're using a virtual environment, activate it first:
```bash
source mcp_env/bin/activate
uvicorn servers:search_app --port 8001 --host 0.0.0.0
uvicorn servers:summary_app --port 8002 --host 0.0.0.0
```

## Run Orchestrator

### Command Line Interface
```bash
python run.py
```

### Web Interface (Flask)

**Important**: Make sure MCP servers are running first (see above).

Start the Flask web application:
```bash
cd "/Users/anupam.purwar/Desktop/mcp-2agent"
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python app.py
```

Or if using virtual environment:
```bash
cd "/Users/anupam.purwar/Desktop/mcp-2agent"
source mcp_env/bin/activate
python app.py
```

Then open your browser and navigate to:
```
http://localhost:5001
```

**Quick Start (All Services):**
```bash
# Terminal 1: Start MCP servers
cd "/Users/anupam.purwar/Desktop/mcp-2agent" && /Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -m uvicorn servers:search_app --port 8001 --host 0.0.0.0 & /Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -m uvicorn servers:summary_app --port 8002 --host 0.0.0.0 &

# Terminal 2: Start Flask app
cd "/Users/anupam.purwar/Desktop/mcp-2agent"
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python app.py
```

The web interface provides:
- Interactive query input with automatic intent detection
- Intent display (shows detected intent: 🔍 Search, 📝 Summarize, 💬 Conversation Query)
- User-driven execution (only runs requested stages)
- Real-time processing status
- Display of search results and summaries
- Confidence scores for each stage
- Past Conversations sidebar (shows all conversation history)
- Clean, modern UI with 90% screen width layout

## Usage Flow

The system is **user-driven** - it only executes stages when requested:

1. **Search**: Ask a question → Only search is executed
   - Example: "Latest trends in speech LLMs"
   - Intent: `search`
   - Executes: `["search"]`

2. **Summarize**: Request summary → Summarizes last 3 agent responses
   - Example: "Summarize" or "Give me a summary"
   - Intent: `summarize`
   - Executes: `["summarize"]`
   - **Note**: Summarizes the last 3 most recent agent responses (search results or summaries) from conversation history
   - **UI Display**: Shows which messages are being summarized, then displays the final summary
   - Messages being summarized appear first (📋 Messages Being Summarized) for transparency
   - Final summary appears after processing is complete (📝 Final Summary)

3. **Conversation Query**: Ask about previous conversations
   - Example: "What did we discuss earlier?" or "Tell me about our previous conversation"
   - Intent: `conversation_query`
   - Executes: `["conversation_query"]`
   - Generates response based on conversation history

## Key Features

### Conversation Context
- Last 5 messages are passed as context to LLM for intent detection and planning
- System maintains full conversation history in CSV
- Past Conversations sidebar shows all previous conversations

### Intent Detection
The system automatically detects user intent using LLM:
- **search**: When user asks a question or wants to search for information
- **summarize**: When user wants a summary of previous responses (gets last 3 most recent)
- **conversation_query**: When user asks about previous conversations

### Summarization
When user requests to summarize:
- System finds the **last 3 most recent agent responses** from conversation history
- Includes both search results and previous summaries (whichever are more recent)
- Displays the messages being summarized on the UI with turn numbers and content preview
- Combines and summarizes them using GPT-4.1-nano
- Returns a concise summary of those responses
- **Always gets the latest 3 responses**, not old cached ones

### State Management
- All conversations are stored in `state.csv`
- System maintains context across queries
- Past Conversations sidebar displays all conversation history
- Each row includes: query, turn number, search results (if any), summary (if any), and confidence scores

## File Structure

```
.
├── app.py              # Flask web application
├── orchestrator.py     # Orchestration logic (intent detection, planning, execution)
├── common.py           # Common utilities (MCP clients, confidence, state machine)
├── servers.py          # MCP servers (search and summary)
├── run.py              # CLI interface
├── state.csv           # Conversation history storage
├── templates/
│   └── index.html     # Web UI
└── static/
    └── css/
        └── style.css   # UI styling
```

## Component Details

### Orchestrator (`orchestrator.py`) - Core Orchestration Engine
The orchestrator is the brain of the system. It manages the entire flow:

**Key Responsibilities:**
- **Intent Detection**: Uses LLM to analyze user queries and determine intent (search, summarize, conversation_query)
  - Function: `detect_intent_with_llm(query, history)` - Uses GPT-4.1-nano with conversation context
- **Execution Planning**: Uses LLM to decide which stages to execute
  - Function: `plan_execution_stages(query, intent, current_state, history)` - Plans minimal execution
- **Stage Execution**: Directly calls MCP clients inline within the orchestration loop
  - For search: Directly calls `search_client.search(query)` via MCP
  - For summarize: Directly calls `summary_client.summarize()` via MCP, processes last 3 agent responses
  - For conversation queries: Calls `generate_conversation_response(query, history)` - Handles conversation queries
- **State Management**: Loads and saves conversation history
  - `load_rows()` - Loads state.csv
  - `save_rows(rows)` - Persists state to CSV
- **Main Orchestration**: Coordinates entire flow
  - Function: `orchestrate(query, intent=None)` - Main entry point

**Key Features:**
- Gets last 5 messages for LLM context
- Only executes minimum required stages
- Direct MCP client calls inline (no wrapper functions)
- Properly identifies last 3 most recent agent responses for summarization
- Returns structured response with metadata

### MCP Clients (`common.py`) - Client Interface to MCP Servers

The MCP clients are HTTP clients that communicate with the MCP servers using JSON-RPC protocol:

**SearchClient** (`SearchClient` class)
- **Purpose**: Makes HTTP POST requests to the Search MCP Server
- **Endpoint**: `http://localhost:8001/rpc`
- **Method**: `search(query)` - Executes web search via Serper API
- **Returns**: `{"text": search_results, "confidence": score, "source": "serper-api"}`

**SummaryClient** (`SummaryClient` class)
- **Purpose**: Makes HTTP POST requests to the Summary MCP Server
- **Endpoint**: `http://localhost:8002/rpc`
- **Method**: `summarize(documents)` - Summarizes documents via OpenAI
- **Returns**: `{"text": summary, "confidence": score, "source": "gpt-4.1-nano"}`

**Generic MCP Client** (`MCPClient` class)
- Base class for all MCP clients
- Method: `call(method, params)` - Generic JSON-RPC call wrapper
- Function: `call_mcp(url, method, params, id)` - Raw HTTP POST implementation

**Utility Functions:**
- `confidence_from_text(text)` - Calculates confidence score based on text length
- `State` enum - Defines conversation states (INIT, SEARCHED, SUMMARIZED, etc.)

### MCP Servers (`servers.py`) - Backend Services

The MCP servers expose JSON-RPC endpoints that handle actual operations:

**Search Server** (`search_app` - FastAPI on port 8001)
- **RPC Method**: `search` - Performs web search
- **Implementation**: Calls Serper API for web search
- **Input**: `{"query": user_query}`
- **Output**: `{"text": snippets, "confidence": score, "source": "serper-api"}`
- **RPC Method**: `list_tools` - Returns available tools (["search"])

**Summary Server** (`summary_app` - FastAPI on port 8002)
- **RPC Method**: `summarize` - Summarizes documents
- **Implementation**: Calls OpenAI GPT-4.1-nano for summarization
- **Input**: `{"documents": [document_list]}`
- **Output**: `{"text": summary, "confidence": score, "source": "gpt-4.1-nano"}`
- **RPC Method**: `list_tools` - Returns available tools (["summarize"])

**Both Servers Use:**
- JSON-RPC 2.0 protocol for communication
- Pydantic models for request validation
- FastAPI framework for HTTP endpoints
- Environment variables for API keys (SERPER_API_KEY, OPENAI_API_KEY)

## Architecture

1. **User Query** → Flask Web UI
2. **Intent Detection** → LLM analyzes query with conversation context (last 5 messages)
3. **Execution Planning** → LLM plans which stages to execute
4. **Stage Execution** → Orchestrator executes planned stages via MCP clients
5. **State Persistence** → Results saved to CSV
6. **Response** → UI displays results with:
   - For Search: Shows search results and confidence score
   - For Summarize: Shows messages being summarized (with turn numbers and content) + final summary
   - For Conversation Query: Shows response based on conversation history

## Recent Updates

### Code Refactoring (Latest)
- **Removed Helper Functions**: `execute_search()` and `execute_summarize()` functions removed
- **Direct MCP Client Calls**: MCP client calls now inlined directly in `orchestrate()` function
- **Simplified Architecture**: Reduced function abstraction layers while maintaining functionality
- **Maintained All Features**: All original functionality preserved, just simplified code structure

### Summarization Improvements
- **Smart Message Selection**: Now correctly identifies and summarizes the last 3 most recent agent responses (by turn number)
- **Flexible Content**: Includes both search results and previous summaries (whichever are more recent)
- **UI Transparency**: Displays the exact messages being summarized before showing the final summary
- **Message Preview**: Shows turn numbers, query previews, and content snippets for each message being summarized
- **Always Current**: Ensures summaries are based on the latest responses, not stale cached data

### Execution Flow Enhancements
- Intent-based execution planning with LLM guidance
- Only executes stages that are actually needed
- Supports three distinct user intents: search, summarize, and conversation queries
- Full conversation history is maintained and accessible

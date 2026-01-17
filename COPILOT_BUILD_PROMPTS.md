# Building MCP-2Agent from Scratch with Claude Haiku 4.5 via GitHub Copilot

This guide provides step-by-step prompts to build the entire MCP-2Agent codebase using GitHub Copilot.

---

## Step 1: Project Setup & Dependencies

### Prompt:
```
Create a Python project for an MCP Agentic System with the following requirements:
1. FastAPI servers for search and summarization
2. Flask web UI
3. LLM-based intent detection and planning using OpenAI GPT-4.1-nano
4. CSV-based conversation history storage

Create a requirements.txt with:
- fastapi
- uvicorn
- requests
- openai
- flask
- python-dotenv
```

**Files to create:**
- `requirements.txt`

---

## Step 2: Common Utilities & MCP Clients

### Prompt:
```
Create a common.py file with the following components:

1. MCPClient base class:
   - call_mcp(url, method, params, id) - Makes HTTP POST requests to MCP servers using JSON-RPC protocol
   - call(method, params) - Generic wrapper method

2. SearchClient class (extends MCPClient):
   - Endpoint: http://localhost:8001/rpc
   - Method: search(query) - Calls MCP search server
   - Returns dict with "text", "confidence", "source"

3. SummaryClient class (extends MCPClient):
   - Endpoint: http://localhost:8002/rpc
   - Method: summarize(documents) - Calls MCP summary server
   - Returns dict with "text", "confidence", "source"

4. Helper functions:
   - confidence_from_text(text) - Calculate confidence based on text length (0-1)
   - State enum with values: INIT, SEARCHED, SUMMARIZED, REVIEWED, INSIGHTED

Include error handling and JSON-RPC 2.0 compliance.
```

**Files to create:**
- `common.py`

---

## Step 3: MCP Servers

### Prompt:
```
Create a servers.py file with two FastAPI-based MCP servers:

1. Search Server (search_app on port 8001):
   - POST /rpc endpoint
   - Methods:
     - list_tools: Returns ["search"]
     - search(query): 
       - Calls Serper API (google.serper.dev/search)
       - Takes top 5 snippets
       - Returns {"text": combined_snippets, "confidence": score, "source": "serper-api"}
   - Use environment variable SERPER_API_KEY

2. Summary Server (summary_app on port 8002):
   - POST /rpc endpoint
   - Methods:
     - list_tools: Returns ["summarize"]
     - summarize(documents):
       - Calls OpenAI GPT-4.1-nano
       - System prompt: "You are a helpful assistant that summarizes documents concisely."
       - Returns {"text": summary, "confidence": score, "source": "gpt-4.1-nano"}
   - Use environment variable OPENAI_API_KEY

3. Use Pydantic RPC model for request validation:
   - jsonrpc: str
   - method: str
   - params: dict
   - id: int

Include confidence_from_text utility from common.py.
```

**Files to create:**
- `servers.py`

---

## Step 4: Orchestrator - Intent Detection & Planning

### Prompt:
```
Create orchestrator.py Part 1 - Intent Detection and Planning Functions:

1. detect_intent_with_llm(query, history=None):
   - Use OpenAI GPT-4.1-nano
   - Analyze user query with last 5 messages as context
   - Return one of: "search", "summarize", "conversation_query"
   - search: User asks a NEW question or wants to search for information
   - summarize: User wants a summary of previous responses
   - conversation_query: User asks about previous conversations (e.g., "What did we discuss?")
   - Include system prompt for intent classification

2. plan_execution_stages(query, intent, current_state=None, history=None):
   - Use OpenAI GPT-4.1-nano
   - Analyze query, intent, current state, and conversation history
   - Return list of stages to execute: ["search"], ["summarize"], ["conversation_query"], etc.
   - CRITICAL RULE: Only execute minimum required stages
   - Parse JSON response for stage list
   - Default fallback based on intent if parsing fails

3. generate_conversation_response(query, history):
   - Use OpenAI GPT-4.1-nano
   - Generate response about previous conversations
   - Use conversation history as context
   - Return {"text": response, "confidence": score}
   - Handle empty history case gracefully

Include proper error handling and LLM response parsing.
```

**Files to create/update:**
- `orchestrator.py` (first part)

---

## Step 5: Orchestrator - State Management

### Prompt:
```
Create orchestrator.py Part 2 - State Management:

Define CSV fields:
FIELDS = ["query", "turn", "search_results", "search_confidence", 
          "summary", "summary_confidence", "reviewed_summary", "review_confidence", 
          "insights", "insights_confidence"]

STATE_FILE = "state.csv"

Functions:
1. load_rows():
   - Load state.csv file
   - Return list of dict rows
   - Return empty list if file doesn't exist

2. save_rows(rows):
   - Write rows to state.csv
   - Filter only FIELDS from each row
   - Use csv.DictWriter with FIELDS as fieldnames

3. get_or_create_row(query, intent=None):
   - Load existing rows
   - For summarize intent: Find most recent row with search results
   - For other intents: Look for matching query
   - If found: Return existing row with latest turn number
   - If not found: Create new row with incremented turn number
   - Return (row, all_rows) tuple

Include proper CSV handling and row creation logic.
```

**Files to update:**
- `orchestrator.py` (add state management functions)

---

## Step 6: Orchestrator - Main Orchestration Engine

### Prompt:
```
Create orchestrator.py Part 3 - Main orchestration logic:

1. Initialize:
   - Load environment variables with load_dotenv()
   - Create OpenAI client
   - Create SearchClient and SummaryClient instances
   - Set STATE_FILE = "state.csv"

2. orchestrate(query, intent=None):
   Main entry point that:
   
   a) Load conversation context:
      - Load all rows from state.csv
      - Get last 5 messages as history
      - Print debug info with message previews
   
   b) Detect intent:
      - If intent is None, call detect_intent_with_llm(query, history)
   
   c) Handle conversation queries separately:
      - If intent == "conversation_query"
      - Call generate_conversation_response(query, history)
      - Create new row with response
      - Save to CSV
      - Return row with metadata
   
   d) Get or create row:
      - Call get_or_create_row(query, intent)
   
   e) Plan execution stages:
      - Call plan_execution_stages(query, intent, row, history)
   
   f) Execute planned stages INLINE:
      For each stage in planned_stages:
      
      - "search" stage:
        - If no search_results in row:
          - Call search_client.search(query) directly
          - Set row["search_results"] = response["text"]
          - Set row["search_confidence"] = response["confidence"]
        - Append "search" to executed_stages
      
      - "summarize" stage:
        - If no summary in row:
          - Load all rows again
          - Find rows with search_results OR summary
          - Sort by turn number, get last 3 most recent
          - Create messages_to_summarize list with turn/query/preview
          - Set row["_summarizing_messages"] = messages_to_summarize
          - Combine last 3 contents into one text
          - Call summary_client.summarize([combined_text]) directly
          - Set row["summary"] = response["text"]
          - Set row["summary_confidence"] = response["confidence"]
        - Append "summary" to executed_stages
        - Save summarizing_messages for UI
   
   g) Save state:
      - Update or append row to rows list
      - Call save_rows(rows)
   
   h) Return row with metadata:
      - Add _executed_stages
      - Add _planned_stages
      - Add _summarizing_messages if available
      - Return row

IMPORTANT: MCP client calls (search_client, summary_client) are called DIRECTLY in the stage execution loop, NOT through separate wrapper functions.
```

**Files to update:**
- `orchestrator.py` (complete the file with main orchestration)

---

## Step 7: Flask Web Application

### Prompt:
```
Create app.py - Flask web application:

1. Initialize Flask app:
   - Load environment variables
   - Import orchestrate, load_rows, detect_intent from orchestrator
   - Create Flask(__name__) app

2. Routes:

   a) GET / (index):
      - Return render_template('index.html')
   
   b) POST /api/query:
      - Extract query from request.json
      - Extract optional intent from request.json
      - Validate query is not empty
      - Get last 5 messages from load_rows()
      - If intent is None, call detect_intent(query, history)
      - Call orchestrate(query, intent)
      - Build response with:
        - success: true
        - query: result['query']
        - turn: result['turn']
        - intent: detected intent
        - planned_stages: result['_planned_stages']
        - executed_stages: result['_executed_stages']
        - last_5_messages: last 5 rows from load_rows()
      - For "search" in executed_stages:
        - Add search_results and search_confidence
      - For "summary" in executed_stages:
        - Add summary and summary_confidence
        - Add summarizing_messages (if available)
      - For "conversation_query" in executed_stages:
        - Add conversation_response
      - Return jsonify(response_data)
      - Error handling: return error JSON with 500 status
   
   c) GET /api/history:
      - Load all rows from load_rows()
      - Return jsonify with all conversation history
      - No limit on history size
      - Error handling included

3. Main:
   - app.run(debug=True, host='0.0.0.0', port=5001)

Include proper error handling with try/except blocks.
```

**Files to create:**
- `app.py`

---

## Step 8: CLI Interface (Optional)

### Prompt:
```
Create run.py - Command line interface:

1. Interactive CLI loop:
   - Import orchestrate, load_rows from orchestrator
   - Load environment variables
   
2. Main loop:
   - Print welcome message
   - While True:
     - Get user input as query
     - If query is empty, skip
     - If query is "exit" or "quit", break
     - Call orchestrate(query)
     - Print result in formatted way:
       - Query and turn number
       - Detected intent
       - Executed stages
       - Search results (if executed)
       - Summary (if executed)
       - Conversation response (if executed)
     - Add separator line between queries

3. Error handling for orchestrate() errors
```

**Files to create:**
- `run.py`

---

## Step 9: HTML Web UI Template

### Prompt:
```
Create templates/index.html - Web UI for conversation:

1. Structure:
   - Container with 90% screen width
   - Two main sections: Chat area (left) and Sidebar (right)
   - Header with title "MCP Agentic System"

2. Chat Area:
   - Messages display area (scrollable)
   - Each message shows:
     - Query
     - Intent display (🔍 Search, 📝 Summarize, 💬 Conversation Query)
     - Results based on executed stages:
       - For search: Show search results with confidence
       - For summarize: Show messages being summarized + final summary
       - For conversation_query: Show response
   - Input area at bottom:
     - Text input field for query
     - Send button
     - Show loading status

3. Sidebar (Past Conversations):
   - Title "Past Conversations"
   - Scrollable list of all conversations
   - Each item shows:
     - Turn number
     - Query preview
     - Summary preview (if available)
   - Click to load conversation

4. JavaScript functionality:
   - Send button click handler
   - POST to /api/query with query and auto-detect intent
   - GET /api/history to load conversation history
   - Display messages with proper formatting
   - Handle loading states
   - Update sidebar on new messages

5. Styling:
   - Clean, modern design
   - Dark theme or light theme
   - Responsive layout
   - Intent indicators with emojis
```

**Files to create:**
- `templates/index.html`

---

## Step 10: CSS Styling

### Prompt:
```
Create static/css/style.css - Styling for web UI:

1. Layout:
   - Main container: 90% width, centered
   - Flexbox layout for chat + sidebar
   - Sidebar width: proportional
   - Chat area: takes remaining width

2. Chat Messages:
   - User messages: styled differently from assistant
   - Intent badges with colors:
     - 🔍 Search: blue
     - 📝 Summarize: green
     - 💬 Conversation Query: purple
   - Results sections with proper spacing
   - Confidence scores displayed

3. Input Area:
   - Sticky at bottom of chat
   - Flex layout for input + button
   - Button with hover effects

4. Sidebar:
   - Scrollable list
   - Hover effects on items
   - Selected state highlighting
   - Clean separators

5. General:
   - Font stack: sans-serif
   - Color scheme: professional
   - Smooth transitions
   - Mobile responsive (optional)
```

**Files to create:**
- `static/css/style.css`

---

## Step 11: Environment Configuration

### Prompt:
```
Create .env.example template file:

OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here

Instructions for users to:
1. Copy .env.example to .env
2. Fill in actual API keys
3. Never commit .env file
```

**Files to create:**
- `.env.example`

**Also create/update:**
- `.gitignore` - Add `.env` to ignore list

---

## Step 12: Testing & Integration

### Prompts for verification:

1. **Test Search Functionality:**
```
Test the search functionality by:
1. Starting MCP servers: 
   - uvicorn servers:search_app --port 8001
   - uvicorn servers:summary_app --port 8002
2. Making a test query "What is AI?" using the Flask app
3. Verify SearchClient successfully calls Serper API
4. Check search results are stored in state.csv
```

2. **Test Summarization:**
```
Test summarization by:
1. Make 3+ search queries
2. Then ask "Summarize"
3. Verify system finds last 3 agent responses
4. Verify SummaryClient successfully summarizes
5. Check summary is stored in state.csv
```

3. **Test Intent Detection:**
```
Test intent detection by:
1. Ask a question: "Latest AI trends" - should detect "search"
2. Ask for summary: "Summarize" or "Give me a summary" - should detect "summarize"
3. Ask about conversation: "What did we discuss?" - should detect "conversation_query"
Verify detected intents match expected values
```

---

## Building Summary

### Complete Build Order:
1. `requirements.txt`
2. `common.py` (MCP clients)
3. `servers.py` (FastAPI servers)
4. `orchestrator.py` (Intent detection, planning, orchestration)
5. `app.py` (Flask web app)
6. `run.py` (CLI interface)
7. `templates/index.html` (Web UI)
8. `static/css/style.css` (Styling)
9. `.env.example` (Configuration template)
10. `.gitignore` (Git configuration)

### Key Architectural Points:
- **MCP Clients** make HTTP POST requests to MCP servers using JSON-RPC 2.0
- **MCP Servers** are FastAPI apps that handle search and summarization
- **Orchestrator** manages the entire flow with LLM-based intent detection and planning
- **Direct MCP Calls**: Search and summarize are called directly in orchestrate() loop, NOT through wrapper functions
- **State Management**: All conversations stored in CSV with full history
- **Context-Aware**: Last 5 messages passed to LLM for intent detection and planning
- **User-Driven**: System only executes what user explicitly requests

---

## Tips for Using These Prompts with Copilot:

1. **Use the prompts in order** - Each step builds on previous ones
2. **Be specific** - Include error handling and edge cases in requests
3. **Ask for clarification** - If Copilot's response doesn't match, ask it to adjust
4. **Test incrementally** - After each file, test that component
5. **Refine iteratively** - Ask Copilot to improve code quality, add features
6. **Request documentation** - Ask for docstrings and comments as you build

Good luck building! 🚀

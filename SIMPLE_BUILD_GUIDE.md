# Building MCP-2Agent - Simple Step-by-Step Guide for Beginners

This guide is for someone with basic Python knowledge who wants to build an MCP Agentic System from scratch.

---

## What We're Building

A chat system that:
1. Searches the web when you ask a question
2. Summarizes previous answers when you ask
3. Remembers all conversations in a file

**Three Main Parts:**
- **Servers** - Run on ports 8001 and 8002, do the actual searching and summarizing
- **Client** - Connects to the servers and asks them to do work
- **Orchestrator** - Takes user questions, decides what to do, talks to client, saves everything

---

## Step 1: Create requirements.txt

### What to do:
Create a simple text file that lists all the libraries we need.

### Prompt for Copilot:
```
Create a requirements.txt file with these dependencies:
- fastapi
- uvicorn
- requests
- openai
- flask
- python-dotenv
```

**File to create:** `requirements.txt`

---

## Step 2: Create common.py (The Client)

### What it does:
This file has code that talks to our servers. Think of it as a messenger.

### Prompt for Copilot:
```
Create a common.py file with:

1. A function called call_mcp(url, method, params):
   - Takes a URL, method name, and some data
   - Sends a POST request to that URL with the data
   - Returns the response as a dictionary
   - The request should have: {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}

2. A SearchClient class:
   - Has a search(query) method
   - Calls call_mcp to http://localhost:8001/rpc
   - Uses method "search" with params {"query": query}
   - Returns the response

3. A SummaryClient class:
   - Has a summarize(documents) method
   - Calls call_mcp to http://localhost:8002/rpc
   - Uses method "summarize" with params {"documents": documents}
   - Returns the response

4. A helper function called confidence_from_text(text):
   - Takes text as input
   - Returns a confidence score between 0 and 1
   - Higher confidence if text is longer
   - For example: length 100 = 0.5, length 200 = 0.8, max 1.0
```

**File to create:** `common.py`

---

## Step 3: Create servers.py (The Workers)

### What it does:
This file has two servers that do the actual work - one searches the web, one summarizes text.

### Prompt for Copilot:
```
Create a servers.py file with two FastAPI servers:

1. Search Server (called search_app, runs on port 8001):
   - Has a POST endpoint at /rpc
   - When it receives:
     - method "list_tools" -> return {"result": ["search"]}
     - method "search" with query -> 
       - Call Serper API at google.serper.dev/search
       - Use SERPER_API_KEY from environment
       - Get the top 5 search results
       - Join them together
       - Return {"result": {"text": joined_results, "confidence": 0.8}}

2. Summary Server (called summary_app, runs on port 8002):
   - Has a POST endpoint at /rpc
   - When it receives:
     - method "list_tools" -> return {"result": ["summarize"]}
     - method "summarize" with documents ->
       - Use OpenAI API (gpt-4.1-nano)
       - Ask it to summarize the documents
       - Use OPENAI_API_KEY from environment
       - Return {"result": {"text": summary_text, "confidence": 0.8}}

3. Use Pydantic to validate incoming requests with fields: jsonrpc, method, params, id

Include necessary imports from fastapi and requests.
```

**File to create:** `servers.py`

---

## Step 4: Create orchestrator.py - Part 1 (Intent Detection)

### What it does:
This file figures out what the user wants to do with their question.

### Prompt for Copilot:
```
Create orchestrator.py with intent detection function:

1. Function: detect_intent(query, history=None):
   - Use OpenAI GPT-4.1-nano to understand what the user wants
   - Analyze the query text
   - Return one of three things: "search", "summarize", or "conversation_query"
   - If user asks a question -> "search" (they want to search for info)
   - If user says "summarize" or "summary" -> "summarize" (they want a summary)
   - If user asks "what did we discuss?" or "what did we talk about?" -> "conversation_query"
   - Use OPENAI_API_KEY from environment
   - Handle errors - if something goes wrong, default to "search"

Test it by calling: detect_intent("Latest AI trends") -> should return "search"
```

**File to create:** `orchestrator.py` (first part)

---

## Step 5: Create orchestrator.py - Part 2 (State Management)

### What it does:
Save and load conversations from a file so we remember everything.

### Prompt for Copilot:
```
Add to orchestrator.py - State management functions:

1. Function: load_rows():
   - Read a file called "state.csv"
   - Return the data as a list of dictionaries
   - If file doesn't exist, return empty list
   - Handle errors gracefully

2. Function: save_rows(rows):
   - Take a list of dictionaries
   - Write them to "state.csv" file
   - Use csv.DictWriter
   - Only save these columns: query, turn, search_results, search_confidence, summary, summary_confidence

3. Function: get_or_create_row(query, intent):
   - Load existing data
   - If this query already exists in file, return that row
   - If not, create a new row with:
     - query: the user's question
     - turn: a number (1, 2, 3, etc.) that goes up each time
     - other fields empty
   - Return the row

The CSV file should have columns: query, turn, search_results, search_confidence, summary, summary_confidence
```

**File to update:** `orchestrator.py`

---

## Step 6: Create orchestrator.py - Part 3 (Main Logic)

### What it does:
The heart of the system - takes user input, decides what to do, calls the client, saves results.

### Prompt for Copilot:
```
Add to orchestrator.py - Main orchestration function:

1. At the top of the file:
   - Import load_dotenv and OpenAI from openai
   - Import SearchClient and SummaryClient from common
   - Load environment variables with load_dotenv()
   - Create clients: search_client = SearchClient() and summary_client = SummaryClient()

2. Function: orchestrate(query):
   This is the main function that does everything:
   
   a) Figure out what user wants:
      - Call detect_intent(query)
      - Store result in 'intent' variable
   
   b) If user is asking about conversation (conversation_query):
      - Create a simple response saying what happened before
      - Save it to CSV
      - Return it
   
   c) If user wants to search or summarize:
      - Get or create row: get_or_create_row(query, intent)
      
      - If intent is "search":
        - Call search_client.search(query)
        - Save results to row["search_results"]
        - Save confidence to row["search_confidence"]
      
      - If intent is "summarize":
        - Load all rows from CSV
        - Find all rows that have search_results
        - Take the last 3 of them
        - Join their text together
        - Call summary_client.summarize([combined_text])
        - Save result to row["summary"]
        - Save confidence to row["summary_confidence"]
      
      - Save the row to CSV using save_rows()
      - Return the row

3. Keep track of what was executed:
   - Add to the returned row: _executed_stages (list of what happened)
   - For example: ["search"] or ["summarize"]

The function should handle errors gracefully.
```

**File to update:** `orchestrator.py`

---

## Step 7: Create app.py (Web Interface)

### What it does:
A simple web server that takes questions from a user and gives answers.

### Prompt for Copilot:
```
Create app.py - A Flask web application:

1. At the top:
   - Import Flask, request, jsonify, render_template
   - Import orchestrate, load_rows from orchestrator
   - Load environment variables
   - Create app = Flask(__name__)

2. Route 1 - Home page (GET /):
   - Return render_template('index.html')

3. Route 2 - Ask a question (POST /api/query):
   - Get the query from the request JSON
   - Validate that query is not empty
   - Call orchestrate(query)
   - Get the result
   - Build a response with:
     - success: true
     - query: the question
     - turn: the turn number
     - intent: what we detected
     - executed_stages: what we did
     - search_results: if we searched
     - search_confidence: confidence score
     - summary: if we summarized
     - summary_confidence: confidence score
   - Return jsonify(response)
   - If there's an error, return error message with 500 status

4. Route 3 - Get history (GET /api/history):
   - Call load_rows()
   - Return all conversations as JSON
   - If error, return empty list

5. Main:
   - app.run(debug=True, host='0.0.0.0', port=5001)

Keep it simple - just return the data.
```

**File to create:** `app.py`

---

## Step 8: Create templates/index.html (Simple Web UI)

### What it does:
A simple HTML page where users can type questions and see answers.

### Prompt for Copilot:
```
Create templates/index.html - A simple web interface:

1. Basic HTML structure with:
   - Title: "Chat with MCP Agent"
   - A container for messages
   - An input box at the bottom to type questions
   - A send button

2. In the messages area, display:
   - The user's question
   - The detected intent (Search, Summarize, or Conversation)
   - The results (search results or summary)
   - Confidence score

3. Add JavaScript to:
   - When user clicks send button:
     - Get the text from input box
     - Send POST request to /api/query
     - Get the response
     - Display it in the messages area
     - Clear the input box
   
   - When page loads:
     - GET /api/history
     - Show all past conversations in a sidebar

4. Make it look nice but keep it simple:
   - Use basic CSS
   - Show messages one after another
   - Different styles for questions and answers
```

**File to create:** `templates/index.html`

---

## Step 9: Create static/css/style.css (Make it Pretty)

### What it does:
Simple styling to make the website look nice.

### Prompt for Copilot:
```
Create static/css/style.css - Simple styling:

1. Container:
   - 90% width
   - Centered
   - Flexbox layout

2. Messages area:
   - Show messages one per line
   - Questions in blue
   - Answers in green
   - Good padding and margins

3. Input area:
   - At the bottom
   - Flex layout: input box + send button
   - Input box takes most space
   - Button on the right

4. Sidebar:
   - Shows past conversations
   - Scrollable list
   - Click to view old conversations

5. Colors and fonts:
   - Clean, professional look
   - Easy to read
   - Light background with dark text (or vice versa)
```

**File to create:** `static/css/style.css`

---

## Step 10: Create .env.example

### What it does:
A template showing what environment variables you need.

### Prompt for Copilot:
```
Create .env.example file with:
OPENAI_API_KEY=your_api_key_here
SERPER_API_KEY=your_api_key_here

This is just a template. Users will copy it to .env and fill in their real keys.
```

**File to create:** `.env.example`

Also create/update `.gitignore`:
```
Add .env to .gitignore so we never commit real API keys
```

---

## Step 11: Create run.py (Command Line Version - Optional)

### What it does:
A simple command-line chat interface if you don't want to use the web browser.

### Prompt for Copilot:
```
Create run.py - A simple command-line chat:

1. Import orchestrate, load_rows from orchestrator
2. Load environment variables
3. Create a loop that:
   - Asks user: "You: "
   - Gets their input
   - Calls orchestrate(query)
   - Prints the result nicely:
     - Show the intent
     - Show search results or summary
     - Show confidence score
   - Repeat until user types "exit"

Keep it simple - just print results to terminal.
```

**File to create:** `run.py`

---

## How to Use These Prompts

1. **Copy one prompt at a time**
2. **Paste it into GitHub Copilot** (or ChatGPT with the file open)
3. **Let it write the code**
4. **Test if it works**
5. **Move to next step**

---

## Testing Checklist

After creating each file, test it:

**After Step 3 (servers.py):**
- Start server 1: `uvicorn servers:search_app --port 8001`
- Start server 2: `uvicorn servers:summary_app --port 8002`
- Do they start without errors?

**After Step 6 (orchestrator.py):**
- Try: `python -c "from orchestrator import orchestrate; orchestrate('What is Python?')"`
- Does it work? Does CSV file get created?

**After Step 7 (app.py):**
- Start: `python app.py`
- Open: `http://localhost:5001`
- Type a question
- Does it work?

---

## Complete File Order

1. `requirements.txt`
2. `common.py`
3. `servers.py`
4. `orchestrator.py`
5. `app.py`
6. `templates/index.html`
7. `static/css/style.css`
8. `.env.example`
9. `.gitignore`
10. `run.py` (optional)

---

## Key Concepts in Simple Terms

**MCP Servers:**
- Separate Python programs that do one job each
- Search server = searches the web
- Summary server = summarizes text
- They're "waiting" for requests on specific addresses

**MCP Client:**
- Code that sends requests to the servers
- Asks: "Hey search server, find info about X"
- Waits for answer
- Returns answer to orchestrator

**Orchestrator:**
- Reads user's question
- Decides: Should we search? Should we summarize?
- Tells client to call the right server
- Saves everything to a file

**Flask App:**
- Simple web server
- Takes requests from browser
- Calls orchestrator
- Sends answer back to browser

---

Good luck! Start with Step 1 and work your way down. 🚀

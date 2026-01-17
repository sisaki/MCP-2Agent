# MCP-2Agent Build Guide - Product Manager Version

**For: Product Manager who needs to describe features to developers**

---

## Feature Overview

We need to build a chat system where users can ask questions and get answers.

### Main Features:
1. **Search Feature** - When user asks a question, find information online
2. **Summarize Feature** - When user asks for summary, condense the answers
3. **Memory Feature** - Remember all conversations

---

## Feature 1: Search Feature

### User Story:
**As a user, I want to type a question and get search results**

### What it should do:
- User types: "What is AI?"
- System finds information online
- Shows results to user
- Saves the question and answer

### Where it happens:
1. User opens website, types question
2. Website sends question to backend
3. Backend searches the web using Serper API
4. Returns results to website
5. Website shows results

### Files needed:
- Search server code (handles the actual search)
- Website code (takes input, shows output)
- Backend code (decides to do search)

---

## Feature 2: Summarize Feature

### User Story:
**As a user, I want to summarize previous answers**

### What it should do:
- User types: "Summarize"
- System looks at last 3 answers given
- Uses AI to create a short summary
- Shows summary to user

### Where it happens:
1. User types "Summarize" in chat
2. Website sends request to backend
3. Backend finds last 3 answers
4. Backend asks AI to summarize them
5. Shows summary to user

### Files needed:
- Summary server code (handles AI summarization)
- Backend code (finds last 3 answers and asks AI)
- Website code (shows summary)

---

## Feature 3: Memory Feature

### User Story:
**As a user, I want the system to remember all my previous conversations**

### What it should do:
- Every question and answer is saved
- Can view conversation history
- System can reference past conversations

### Where it happens:
1. Every time user asks something, save it
2. Save the answer too
3. Store in a file (simple database)
4. Show history in sidebar

### Files needed:
- Code that saves to file (state management)
- Code that loads from file (when page starts)

---

## System Architecture (Simple Version)

```
User Browser
    ↓
Website Interface (shows chat, takes input)
    ↓
Backend Server (decides what to do)
    ↓
┌─────────────────┬──────────────────┐
↓                 ↓
Search Server     Summary Server
    ↓                 ↓
Serper API        OpenAI API
(finds info)      (summarizes text)
```

---

## What Each Part Does

### Part 1: Website (User sees this)
- Shows a chat interface
- Let's user type questions
- Displays answers
- Shows conversation history on the side

### Part 2: Backend Server (Brain of system)
- Takes user's question
- Decides: Should we search? Should we summarize?
- Tells Search Server or Summary Server what to do
- Saves everything to memory

### Part 3: Search Server (Worker - Port 8001)
- Receives request: "Find info about AI"
- Calls Serper API
- Gets results back
- Sends results to Backend Server

### Part 4: Summary Server (Worker - Port 8002)
- Receives request: "Summarize these 3 answers"
- Calls OpenAI API
- Gets summary back
- Sends summary to Backend Server

### Part 5: Memory (File storage)
- Simple file that stores all questions and answers
- Backend saves to it after each question
- Backend reads from it to get history

---

## Features by Priority

### Must Have (Priority 1):
1. ✅ User can ask a question → Get search results
2. ✅ System saves all questions and answers
3. ✅ User can see conversation history

### Nice to Have (Priority 2):
1. ✅ User can ask for summary → Get summary of last 3 answers
2. ✅ Show confidence score for each answer
3. ✅ Command-line interface (for testing)

### Future (Priority 3):
1. User can delete conversations
2. User can export conversations
3. Multi-user support

---

## User Flows

### Flow 1: Search and View
1. User opens website
2. Types: "What is Python?"
3. System shows search results
4. Results saved automatically
5. User sees results with confidence score

### Flow 2: Summarize Previous Answers
1. User asks 3 questions (gets 3 answers)
2. User types: "Summarize"
3. System takes those 3 answers
4. Creates short summary
5. Shows summary to user
6. Summary saved

### Flow 3: View History
1. User opens website
2. Sidebar shows all previous conversations
3. User can click to see old answers
4. User can ask follow-up questions

---

## Technical Requirements (for developers)

### Backend needs to:
- Listen for user questions
- Decide what kind of question it is (search vs summarize)
- Call the right server (Search or Summary)
- Save everything to a file
- Return results to website

### Search Server needs to:
- Listen for search requests
- Use Serper API to find info
- Return results in consistent format
- Give confidence score

### Summary Server needs to:
- Listen for summarize requests
- Use OpenAI API to summarize
- Return summary in consistent format
- Give confidence score

### Website needs to:
- Load on localhost:5001
- Show chat interface
- Send questions to backend
- Display results
- Show history sidebar
- Auto-refresh conversation history

### Memory needs to:
- Save as simple CSV file
- One row per conversation turn
- Include: question, answer, type (search/summary), confidence

---

## API Contracts (Backend talks to Servers)

### When Backend Calls Search Server:
```
Send: {"method": "search", "query": "What is AI?"}
Get back: {"text": "search results here", "confidence": 0.95}
```

### When Backend Calls Summary Server:
```
Send: {"method": "summarize", "documents": ["answer1", "answer2", "answer3"]}
Get back: {"text": "summary here", "confidence": 0.90}
```

---

## Data that Gets Saved

Every conversation turn saves:
- Question user asked
- Turn number (1, 2, 3, etc.)
- Search results (if we searched)
- Confidence score from search
- Summary (if we summarized)
- Confidence score from summary

Example row in file:
```
Question: "What is AI?"
Turn: 1
Search Results: "Artificial Intelligence is..."
Search Confidence: 0.95
Summary: ""
Summary Confidence: ""
```

---

## Files to Create

1. **requirements.txt** - List of libraries needed
2. **servers.py** - Code for Search and Summary servers
3. **common.py** - Code that talks to servers
4. **orchestrator.py** - Brain that decides what to do
5. **app.py** - Website backend
6. **index.html** - Website frontend (what user sees)
7. **style.css** - Website styling (colors, fonts)
8. **.env.example** - Template for API keys

---

## Dependencies (Libraries)

- **FastAPI** - Make the servers
- **Uvicorn** - Run the servers
- **Flask** - Website backend
- **Requests** - Talk to APIs
- **OpenAI** - Talk to OpenAI
- **python-dotenv** - Load API keys

---

## Decisions to Make Before Building

1. **What port for website?** → 5001
2. **What port for search server?** → 8001
3. **What port for summary server?** → 8002
4. **How many previous answers to summarize?** → Last 3
5. **Confidence score: high = ?** → 0.9-1.0
6. **Conversation history limit?** → No limit, save everything

---

## Success Criteria

✅ **User can ask question → Gets search results**
✅ **User can ask for summary → Gets summary**
✅ **All conversations saved and can be viewed**
✅ **Website works at localhost:5001**
✅ **Servers work at localhost:8001 and 8002**
✅ **No errors when user asks questions**
✅ **Confidence scores show correctly**

---

## Testing Plan

### Test 1: Search Works
- User asks: "What is Python?"
- Should see search results
- Should be saved in file

### Test 2: Summarize Works
- User asks 3 questions
- User asks: "Summarize"
- Should see summary of all 3
- Should be saved

### Test 3: History Works
- User opens website
- Should see all past conversations in sidebar
- Should be able to see old answers

### Test 4: Servers Work
- Start servers on ports 8001 and 8002
- Should run without errors
- Should respond to requests

---

## Deployment Checklist

- [ ] All files created
- [ ] Libraries installed
- [ ] API keys configured in .env
- [ ] Website loads at localhost:5001
- [ ] Servers start without errors
- [ ] Search works end-to-end
- [ ] Summarize works end-to-end
- [ ] History saves and loads
- [ ] No errors in console

---

## Quick Reference

| Feature | Port | What it does |
|---------|------|-------------|
| Website | 5001 | Shows chat to user |
| Search Server | 8001 | Searches the web |
| Summary Server | 8002 | Summarizes text |
| Memory | CSV file | Saves conversations |

---

## For Developers: Translation Guide

When I say... | I mean...
--- | ---
"User types question" | Backend receives POST request to /api/query
"System decides what to do" | Code runs detect_intent() function
"Tell Search Server what to do" | Call search_client.search(query)
"Tell Summary Server what to do" | Call summary_client.summarize(documents)
"Save to memory" | Write row to state.csv
"Show in sidebar" | Return conversation history in /api/history

---

Good luck building! 🚀

**Key reminder: Build in this order**
1. Servers (8001, 8002)
2. Backend (orchestrator)
3. Website (Flask + HTML)
4. Test everything

Start with servers because website depends on them!

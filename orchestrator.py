"""Orchestration logic: LLM planning and execution orchestration"""
import csv
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from common import SearchClient, SummaryClient

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STATE_FILE = "state.csv"

FIELDS = [
    "query", "turn",
    "search_results", "search_confidence",
    "summary", "summary_confidence",
    "reviewed_summary", "review_confidence",
    "insights", "insights_confidence"
]

# Initialize MCP Clients
search_client = SearchClient()
summary_client = SummaryClient()


# LLM Planning Functions
def detect_intent_with_llm(query, history=None):
    """
    Use LLM (GPT-4.1-nano) to analyze user query and detect intent.
    
    Args:
        query: The user's query
        history: List of last N messages (each with 'query' and optionally 'summary')
    
    Returns one of: "search", "summarize", "conversation_query"
    """
    context = ""
    if history and len(history) > 0:
        context = "\n\nRecent conversation history:\n"
        for i, msg in enumerate(history[-5:], 1):  # Last 5 messages
            context += f"{i}. Query: {msg.get('query', '')}\n"
            if msg.get('summary'):
                context += f"   Summary: {msg.get('summary', '')[:100]}...\n"
    
    prompt = f"""Analyze the following user query and determine their intent.{context}

User Query: "{query}"

The user wants to:
- "search" - if they're asking a NEW question or want to search for NEW information
- "summarize" - if they want a summary or brief of search results
- "conversation_query" - if they're asking ABOUT previous conversations (e.g., "what did we discuss?", "tell me about our previous conversation", "what was the last thing we talked about?", "remind me what we searched for")

Respond with ONLY one word: search, summarize, or conversation_query
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes user queries to determine intent. Always respond with exactly one word: search, summarize, or conversation_query."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        text = response.choices[0].message.content.strip().lower()
        
        valid_intents = ["search", "summarize", "conversation_query"]
        for intent in valid_intents:
            if intent in text:
                return intent
        
        return "search"
    except Exception as e:
        print(f"Error in LLM intent detection: {e}")
        return "search"


def plan_execution_stages(query, intent, current_state=None, history=None):
    """
    Use LLM (GPT-4.1-nano) to plan which execution stages should run.
    
    Args:
        query: The user's query
        intent: The detected intent (search, summarize)
        current_state: Optional dict with current state (what's already been done)
        history: List of last N messages for context
    
    Returns:
        List of stages to execute: ["search"], ["search", "summarize"], etc.
    """
    state_info = ""
    has_search = False
    has_summary = False
    
    if current_state:
        completed = []
        if current_state.get("search_results"):
            completed.append("search")
            has_search = True
        if current_state.get("summary"):
            completed.append("summary")
            has_summary = True
        if completed:
            state_info = f"\n\nAlready completed stages: {', '.join(completed)}"
            state_info += f"\nAvailable context: search_results={'yes' if has_search else 'no'}, summary={'yes' if has_summary else 'no'}"
    
    context = ""
    if history and len(history) > 0:
        context = "\n\nRecent conversation history:\n"
        for i, msg in enumerate(history[-5:], 1):  # Last 5 messages
            context += f"{i}. Query: {msg.get('query', '')}\n"
            if msg.get('summary'):
                context += f"   Summary: {msg.get('summary', '')[:100]}...\n"
    
    prompt = f"""You are a planning agent. Based on the user's query and intent, 
    determine EXACTLY which stages should be executed.{context}

User Query: "{query}"
Detected Intent: {intent}
{state_info}

Available stages:
- "search" - Search for NEW information
- "summarize" - Summarize last 3 agent responses from conversation history

CRITICAL RULES:
1. If intent is "search" AND user explicitly asks for NEW search, execute ["search"]
2. If intent is "summarize", execute ONLY ["summarize"] (summarizes last 3 agent responses)
3. ONLY execute the minimum stages needed - reuse existing context whenever possible

Respond with ONLY a JSON array of stage names, e.g., ["search"] or ["search", "summarize"]
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a planning agent. Always respond with a valid JSON array of stage names. Example: [\"search\"] or [\"search\", \"summarize\"]. Do not execute more stages than necessary."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        text = response.choices[0].message.content.strip()
        
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        stages = json.loads(text)
        
        valid_stages = ["search", "summarize"]
        stages = [s for s in stages if s in valid_stages]
        
        if not stages:
            if intent == "search":
                return ["search"]
            elif intent == "summarize":
                return ["summarize"]
            return ["search"]
        
        return stages
    except Exception as e:
        print(f"Error in LLM planning: {e}")
        if intent == "search":
            return ["search"]
        elif intent == "summarize":
            return ["summarize"]
        return ["search"]


def plan(state, user_intent):
    """
    Plan required states using LLM.
    (Legacy function - kept for compatibility)
    """
    prompt = f"""
State: {state}
User intent: {user_intent}

Return JSON list of required states:
INIT, SEARCHED, SUMMARIZED, REVIEWED, INSIGHTED
"""
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that returns JSON responses."},
            {"role": "user", "content": prompt}
        ]
    )
    text = response.choices[0].message.content.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


# Parallel insights (for future use)
def parallel_insights(context, insights_client):
    """
    Generate parallel insights using MCP client.
    
    Args:
        context: The context text to generate insights from
        insights_client: InsightsClient instance
    """
    prompts = [
        f"Technical insights:\n{context}",
        f"Research insights:\n{context}",
        f"Future directions:\n{context}",
    ]
    
    def safe_call(prompt):
        try:
            return insights_client.insights(prompt)
        except Exception as e:
            return {"text": f"Error: {str(e)}", "error": True}
    
    results = []
    with ThreadPoolExecutor() as ex:
        results = list(ex.map(safe_call, prompts))
    
    successful_results = [r["text"] for r in results if not r.get("error", False)]
    if successful_results:
        return "\n\n".join(successful_results)
    else:
        error_messages = [r.get("text", "Unknown error") for r in results]
        return f"All insight generation attempts failed:\n" + "\n".join(error_messages)


# Orchestration Functions
def load_rows():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE) as f:
        return list(csv.DictReader(f))


def save_rows(rows):
    with open(STATE_FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        # Only write fields that are in FIELDS
        filtered_rows = [{k: v for k, v in row.items() if k in FIELDS} for row in rows]
        w.writerows(filtered_rows)


def detect_intent(query, history=None):
    """
    Detect user intent from query using LLM (GPT-4.1-nano).
    The LLM analyzes the user query and determines the appropriate intent.
    """
    return detect_intent_with_llm(query, history)


def get_or_create_row(query, intent=None):
    """
    Get existing row for conversation context or create new one.
    For conversation continuity, uses the most recent row with context
    if the user is asking for summarize (not a new search).
    """
    rows = load_rows()
    
    if intent == "summarize":
        rows_with_context = [r for r in rows if r.get("search_results", "").strip()]
        if rows_with_context:
            latest = max(rows_with_context, key=lambda x: int(x.get("turn", "0")))
            N=3
            latest_n = sorted(
                        rows_with_context,
                        key=lambda x: int(x.get("turn", 0)),
                        reverse=True
                    )[:N]
            row = latest_n[0].copy()  # Use the most recent row
            row["query"] = query
            return row, rows
    
    matching_rows = [r for r in rows if r.get("query") == query]
    if matching_rows:
        latest = max(matching_rows, key=lambda x: int(x.get("turn", "0")))
        return latest, rows
    
    turn = max([int(r["turn"]) for r in rows if r.get("turn", "").strip().isdigit()], default=0) + 1
    row = dict.fromkeys(FIELDS, "")
    row["query"], row["turn"] = query, str(turn)
    return row, rows


def execute_search(query, row):
    """Execute search stage using MCP client"""
    if row.get("search_results"):
        return row
    
    r = search_client.search(query)
    row["search_results"] = r["text"]
    row["search_confidence"] = str(r["confidence"])
    return row


def execute_summarize(row):
    """Execute summarize stage - summarizes last 3 agent responses"""
    if row.get("summary"):
        return row
    
    # Get all rows to find last 3 agent responses
    rows = load_rows()
    
    # Get last 3 rows that have either search_results or summaries (agent responses)
    # These are rows that represent actual agent outputs (not just conversation queries)
    rows_with_content = [r for r in rows if r.get("search_results", "").strip() or r.get("summary", "").strip()]
    if len(rows_with_content) == 0:
        raise ValueError("Cannot summarize: no previous agent responses available. Please have some conversations first.")
    
    # Sort by turn number (oldest to newest) and get the last 3 most recent responses
    sorted_rows = sorted(rows_with_content, key=lambda x: int(x.get("turn", "0")), reverse=False)
    last_3_summaries = sorted_rows[-3:]
    
    # Extract text from search_results or summaries for display
    messages_to_summarize = []
    summary_texts = []
    for r in last_3_summaries:
        # Use summary if available, otherwise use search_results
        content = r.get("summary", "") or r.get("search_results", "")
        summary_texts.append(content)
        messages_to_summarize.append({
            "query": r.get("query", ""),
            "summary": content[:200] + "..." if len(content) > 200 else content,
            "turn": r.get("turn", "")
        })
    
    # Save the actual messages being summarized for UI
    row["_summarizing_messages"] = messages_to_summarize
    
    # Combine the content for summarization
    combined_text = "\n\n".join([f"Response {i+1}: {text}" for i, text in enumerate(summary_texts)])
    
    # Summarize the combined text
    r = summary_client.summarize([combined_text])
    row["summary"] = r["text"]
    row["summary_confidence"] = str(r["confidence"])
    return row


def generate_conversation_response(query, history):
    """
    Generate a response about previous conversations using LLM.
    
    Args:
        query: The user's query about previous conversations
        history: List of previous messages
    
    Returns:
        Dict with response text and confidence
    """
    if not history or len(history) == 0:
        return {
            "text": "I don't have any previous conversation history to reference. Please start a new search or query.",
            "confidence": 1.0
        }
    
    # Build conversation context
    context = "Previous conversation history:\n\n"
    for i, msg in enumerate(history, 1):
        context += f"Conversation {i}:\n"
        context += f"  Query: {msg.get('query', 'N/A')}\n"
        if msg.get('search_results'):
            context += f"  Search Results: {msg.get('search_results', '')[:200]}...\n"
        if msg.get('summary'):
            context += f"  Summary: {msg.get('summary', '')}\n"
        context += "\n"
    
    prompt = f"""Based on the conversation history below, answer the user's question about previous conversations.

{context}

User's question: "{query}"

Provide a helpful and concise answer based on the conversation history. If the question cannot be answered from the history, politely say so.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions about previous conversations. Use the conversation history to provide accurate and helpful responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        text = response.choices[0].message.content.strip()
        
        # Calculate confidence based on response length
        from common import confidence_from_text
        confidence = confidence_from_text(text)
        
        return {
            "text": text,
            "confidence": confidence
        }
    except Exception as e:
        print(f"Error generating conversation response: {e}")
        return {
            "text": f"I encountered an error while processing your question about previous conversations: {str(e)}",
            "confidence": 0.5
        }


def orchestrate(query, intent=None):
    """
    Orchestrate based on LLM planning.
    Only executes the stages planned by the LLM.
    Uses MCP clients for all server interactions.
    """
    # Get last 5 messages for context
    rows = load_rows()
    history = rows[-5:] if len(rows) > 5 else rows
    
    # Print last 5 messages for debugging
    print("\n" + "="*60)
    print("LAST 5 MESSAGES (CONTEXT):")
    print("="*60)
    if history:
        for i, msg in enumerate(history, 1):
            print(f"\n{i}. Query: {msg.get('query', 'N/A')}")
            if msg.get('summary'):
                print(f"   Summary: {msg.get('summary', '')[:150]}...")
            if msg.get('search_results'):
                print(f"   Has search results: Yes")
    else:
        print("No previous messages")
    print("="*60 + "\n")
    
    if intent is None:
        intent = detect_intent(query, history)
    
    # Handle conversation queries separately
    if intent == "conversation_query":
        response = generate_conversation_response(query, history)
        row = dict.fromkeys(FIELDS, "")
        turn = max([int(r["turn"]) for r in rows if r.get("turn", "").strip().isdigit()], default=0) + 1
        row["query"] = query
        row["turn"] = str(turn)
        row["summary"] = response["text"]  # Store response in summary field for display
        row["summary_confidence"] = str(response["confidence"])
        rows.append(row)
        save_rows(rows)
        row["_executed_stages"] = ["conversation_query"]
        row["_planned_stages"] = ["conversation_query"]
        row["_conversation_response"] = response["text"]
        return row
    
    row, rows = get_or_create_row(query, intent)
    
    planned_stages = plan_execution_stages(query, intent, row, history)
    
    executed_stages = []
    summarizing_messages = None
    for stage in planned_stages:
        if stage == "search":
            row = execute_search(query, row)
            executed_stages.append("search")
        elif stage == "summarize":
            row = execute_summarize(row)
            executed_stages.append("summary")
            # Capture the messages being summarized for UI
            summarizing_messages = row.get("_summarizing_messages")
    
    updated = False
    for i, r in enumerate(rows):
        if r.get("turn") == row["turn"]:
            rows[i] = row
            updated = True
            break
    
    if not updated:
        rows.append(row)
    
    save_rows(rows)
    
    row["_executed_stages"] = executed_stages
    row["_planned_stages"] = planned_stages
    if summarizing_messages:
        row["_summarizing_messages"] = summarizing_messages
    
    return row


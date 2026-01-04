"""Common utilities: confidence calculation, MCP clients, and state machine"""
import requests
import logging
from enum import Enum

logger = logging.getLogger(__name__)


# Confidence calculation
def confidence_from_text(text):
    length = len(text.split())
    return round(min(0.95, max(0.4, length / 200)), 2)


# State machine
class State(Enum):
    INIT = "INIT"
    SEARCHED = "SEARCHED"
    SUMMARIZED = "SUMMARIZED"
    REVIEWED = "REVIEWED"
    INSIGHTED = "INSIGHTED"


def next_state(row):
    if not row["search_results"]:
        return State.INIT
    if not row["summary"]:
        return State.SEARCHED
    if not row["reviewed_summary"]:
        return State.SUMMARIZED
    if not row["insights"]:
        return State.REVIEWED
    return State.INSIGHTED


# MCP Client
def call_mcp(url, method, params, _id=1):
    """
    Make an RPC call to an MCP server via HTTP POST.
    
    Args:
        url: The MCP server endpoint URL (e.g., "http://localhost:8001/rpc")
        method: The RPC method name (e.g., "search", "summarize")
        params: The method parameters as a dict
        _id: Request ID for JSON-RPC
    
    Returns:
        The result from the MCP server response
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": _id
    }
    
    logger.debug(f"Calling MCP server at {url} with method '{method}'")
    
    r = requests.post(url, json=payload)
    r.raise_for_status()
    
    response = r.json()
    if "error" in response:
        error_msg = response['error'].get('message', 'Unknown error')
        logger.error(f"MCP server error: {error_msg}")
        raise Exception(f"MCP Error: {error_msg}")
    
    logger.debug(f"MCP server response received for method '{method}'")
    return response["result"]


class MCPClient:
    """MCP Client wrapper for server interactions"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        logger.info(f"Initialized MCP client for server: {base_url}")
    
    def call(self, method, params, _id=1):
        """Call an MCP method on the server."""
        return call_mcp(self.base_url, method, params, _id)
    
    def list_tools(self):
        """List available tools on this MCP server"""
        return self.call("list_tools", {})


class SearchClient(MCPClient):
    """Client for Search MCP Server"""
    
    def __init__(self, base_url="http://localhost:8001/rpc"):
        super().__init__(base_url)
    
    def search(self, query):
        """Execute search by calling the MCP server."""
        logger.info(f"SearchClient: Calling MCP server at {self.base_url} with query: {query[:50]}...")
        return self.call("search", {"query": query})


class SummaryClient(MCPClient):
    """Client for Summary MCP Server"""
    
    def __init__(self, base_url="http://localhost:8002/rpc"):
        super().__init__(base_url)
    
    def summarize(self, documents):
        """Execute summarization by calling the MCP server."""
        logger.info(f"SummaryClient: Calling MCP server at {self.base_url} with {len(documents)} documents")
        return self.call("summarize", {"documents": documents})


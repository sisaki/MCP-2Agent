"""MCP Servers: Search and Summary servers"""
import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from common import confidence_from_text

load_dotenv()

# Search Server
search_app = FastAPI()
SERPER_KEY = os.getenv("SERPER_API_KEY")


class RPC(BaseModel):
    jsonrpc: str
    method: str
    params: dict
    id: int


@search_app.post("/rpc")
def search_rpc(req: RPC):
    if req.method == "list_tools":
        return {"result": ["search"], "id": req.id}

    if req.method == "search":
        q = req.params["query"]
        r = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_KEY},
            json={"q": q, "num": 5}
        ).json()
        snippets = [x["snippet"] for x in r.get("organic", [])]
        text = " || ".join(snippets)
        return {
            "result": {
                "text": text,
                "confidence": confidence_from_text(text),
                "source": "serper-api"
            },
            "id": req.id
        }


# Summary Server
summary_app = FastAPI()
summary_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@summary_app.post("/rpc")
def summary_rpc(req: RPC):
    if req.method == "list_tools":
        return {"result": ["summarize"], "id": req.id}

    if req.method == "summarize":
        docs = "\n".join(req.params["documents"])
        response = summary_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes documents concisely."},
                {"role": "user", "content": f"Summarize:\n{docs}"}
            ]
        )
        text = response.choices[0].message.content
        return {
            "result": {
                "text": text,
                "confidence": confidence_from_text(text),
                "source": "gpt-4.1-nano"
            },
            "id": req.id
        }


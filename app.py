"""
Home Credit AI Voice Agent - FastAPI Application Server
Serves Web Dashboard UI, Voice Agent Chat API, Retell AI Webhooks, and Test Suite Endpoint.
"""

import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from agent.conversational_agent import ConversationalAgent
from tests.test_matrix import run_all_tests, TestHomeCreditVoiceAgent
import unittest

app = FastAPI(
    title="Home Credit AI Voice Agent",
    description="Pre-approved Loan Against Property (LAP) Voice Agent Server",
    version="1.0.0"
)

# Mount Static Files
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# In-Memory Active Sessions Store
sessions: Dict[str, ConversationalAgent] = {}

def get_or_create_session(session_id: str) -> ConversationalAgent:
    if session_id not in sessions:
        sessions[session_id] = ConversationalAgent(customer_name="Rajesh Sharma")
    return sessions[session_id]

# Request Schemas
class ChatRequest(BaseModel):
    session_id: str = "default_session"
    customer_utterance: str

class ResetRequest(BaseModel):
    session_id: str = "default_session"

# Web Dashboard Route
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Home Credit Voice Agent Server Running</h1>")

# Chat API Endpoint
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    agent = get_or_create_session(req.session_id)
    response_data = agent.process_utterance(req.customer_utterance)
    return JSONResponse(content=response_data)

# Retell AI / Bolna Webhook API Endpoint
@app.post("/api/retell-webhook")
async def retell_webhook(request: Request):
    """
    Webhook handler for Retell AI / Bolna custom LLM voice server.
    Converts incoming payload to agent response format.
    """
    body = await request.json()
    
    call_id = body.get("call", {}).get("call_id") or body.get("session_id", "retell_default")
    transcript = body.get("args", {}).get("transcript") or body.get("user_utterance") or body.get("transcript", "")

    if not transcript:
        return JSONResponse(content={"response_type": "text", "content": "Hello! How can I assist you with your Home Credit pre-approved loan today?"})

    agent = get_or_create_session(call_id)
    result = agent.process_utterance(transcript)

    # Retell AI expected response payload format
    return JSONResponse(content={
        "response_type": "text",
        "content": result["agent_response"],
        "end_call": result["action"] in ["HANDOFF", "DISQUALIFIED", "TRANSFER", "CALLBACK"]
    })

# Session Reset Endpoint
@app.post("/api/reset")
async def reset_endpoint(req: ResetRequest):
    if req.session_id in sessions:
        sessions[req.session_id].reset()
    return JSONResponse(content={"status": "reset_successful", "session_id": req.session_id})

# Get Current Session State Endpoint
@app.get("/api/state")
async def get_state_endpoint(session_id: str = "default_session"):
    agent = get_or_create_session(session_id)
    return JSONResponse(content=agent.state.to_dict())

# Run Automated Test Matrix Endpoint
@app.post("/api/run-tests")
async def run_tests_endpoint():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHomeCreditVoiceAgent)
    test_results = []

    for test in suite:
        test_name = test._testMethodName
        doc_str = test._testMethodDoc or test_name
        
        single_suite = unittest.TestSuite([test])
        runner = unittest.TextTestRunner(verbosity=0)
        res = runner.run(single_suite)

        passed = res.wasSuccessful()
        test_results.append({
            "name": test_name.replace("test_", "").replace("_", " ").title(),
            "description": doc_str,
            "passed": passed
        })

    total = len(test_results)
    passed_count = sum(1 for t in test_results if t["passed"])
    
    return JSONResponse(content={
        "total": total,
        "passed": passed_count,
        "failures": total - passed_count,
        "results": test_results
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# Home Credit AI Voice Agent — Loan Against Property (LAP)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-16%2F16%20Passed-brightgreen.svg)]()
[![Voice Platform](https://img.shields.io/badge/Voice%20Platform-Retell%20AI%20%2F%20Bolna-orange.svg)]()

An enterprise-grade, conversational **AI Voice Agent** for **Home Credit India** designed to contact existing customers regarding a pre-approved **Loan Against Property (LAP)** offer of up to **₹75 Lakh (₹75,00,000)**.

---

## 📑 Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Architectural Diagram](#2-architectural-diagram)
- [3. Key Business Rules & 7-Point Eligibility Engine](#3-key-business-rules--7-point-eligibility-engine)
- [4. Repository Structure](#4-repository-structure)
- [5. System Prompt & Dynamic Variables](#5-system-prompt--dynamic-variables)
- [6. Retell AI / Bolna Voice Platform Integration](#6-retell-ai--bolna-voice-platform-integration)
- [7. Setup & Local Installation](#7-setup--local-installation)
- [8. Interactive Web Dashboard & Voice Sandbox](#8-interactive-web-dashboard--voice-sandbox)
- [9. Test Matrix Suite (16 Scenarios)](#9-test-matrix-suite-16-scenarios)
- [10. Submission Checklist](#10-submission-checklist)

---

## 1. Project Overview

The Home Credit AI Voice Agent contacts existing customers with pre-approved LAP offers up to ₹75 Lakh. The agent handles natural conversation, out-of-order responses, corrections, interruptions, product inquiries via RAG, and enforces strict business disqualification rules.

### Capabilities
- **Strict 7-Point Eligibility Verification**: Collects Property Type, Ownership, Original Documents, Loan Amount, Occupation/Income Mode, Property Market Value, and Tenure.
- **Immediate Disqualification**: Instantly ends call cleanly if customer fails mandatory rules (Agricultural land, Cash income, Missing original papers, Tenure <3 or >15 years).
- **Loan Amount Negotiation**: Offers maximum cap of ₹75 Lakh if customer requests > ₹75 Lakh (e.g. ₹90 Lakh).
- **Balance Transfer Specialist Handoff**: Detects existing property loans or EMI reduction requests and transfers call to a specialist.
- **Busy Customer Flow**: Captures preferred callback time and ends call politely.
- **RAG Knowledge Base Retrieval**: Uses RAG to answer product questions accurately without inventing interest rates or terms.
- **Final Handoff Gate**: Ensures senior expert handoff occurs **only** when all 7 eligibility points are verified, no disqualifications occur, and no transfer is required.

---

## 2. Architectural Diagram

```text
                     +---------------------------+
                     |  Customer Voice Call      |
                     |  (Retell AI / Bolna STT)  |
                     +-------------+-------------+
                                   |
                                   v
                     +-------------+-------------+
                     | FastAPI Server (app.py)    |
                     | Webhook / Chat Endpoint   |
                     +-------------+-------------+
                                   |
                                   v
                     +-------------+-------------+
                     | Conversational Agent      |
                     | (Multi-Entity Parser)     |
                     +-------------+-------------+
                                   |
           +-----------------------+-----------------------+
           |                       |                       |
           v                       v                       v
+----------+----------+  +---------+----------+  +---------+----------+
|  Internal State     |  |  RAG Engine        |  |  Eligibility       |
|  Management         |  |  (knowledge.txt)   |  |  Rules Engine      |
|  (agent/state.py)   |  |  (rag_engine.py)   |  | (eligibility.py)  |
+----------+----------+  +---------+----------+  +---------+----------+
           |                       |                       |
           +-----------------------+-----------------------+
                                   |
                                   v
                     +-------------+-------------+
                     | Evaluated Action &        |
                     | Response Decision         |
                     +-------------+-------------+
                                   |
     +-----------------+-----------+-----------+-----------------+
     |                 |                       |                 |
     v                 v                       v                 v
[CONTINUE]        [DISQUALIFIED]          [TRANSFER]        [HANDOFF]
Ask next missing  Politely explain &      Transfer to       Senior Expert
eligibility q     end call                Specialist        Handoff Gate
```

---

## 3. Key Business Rules & 7-Point Eligibility Engine

### The 7 Eligibility Criteria

| # | Data Point | Allowed Values | Disqualification Condition |
|---|---|---|---|
| 1 | **Property Type** | Residential, Commercial, Industrial | **Agricultural** -> Disqualify Immediately |
| 2 | **Ownership Status** | Sole ownership, Joint ownership | Both eligible |
| 3 | **Original Documents** | Available (`True`) | **Unavailable (`False`)** -> Disqualify Immediately |
| 4 | **Loan Amount** | Up to ₹75,00,000 (₹75 Lakh) | > ₹75 Lakh -> Offer ₹75 Lakh cap. Reject if declined |
| 5 | **Occupation & Income Mode** | Salaried, Self-employed (Bank) | **Cash Income** -> Disqualify Immediately |
| 6 | **Property Market Value** | Collected (Approx market value) | No minimum market-value threshold applied |
| 7 | **Tenure** | 3 years to 15 years (inclusive) | **< 3 years or > 15 years** -> Disqualify Immediately |

---

## 4. Repository Structure

```text
home-credit-voice-agent/
│
├── app.py                      # FastAPI Web server, Chat API, Webhook & Test Runner
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── README.md                   # Complete documentation
│
├── prompts/
│   ├── __init__.py
│   └── system_prompt.py        # System prompt builder & full template
│
├── agent/
│   ├── __init__.py
│   ├── state.py                # Customer state management class
│   ├── eligibility.py          # Eligibility rules engine
│   └── conversational_agent.py # Agent orchestrator connecting state/RAG/rules
│
├── rag/
│   ├── __init__.py
│   ├── knowledge.txt           # RAG Knowledge base for Home Credit LAP
│   └── rag_engine.py           # Knowledge retriever engine
│
├── tests/
│   ├── __init__.py
│   └── test_matrix.py          # 16-Scenario Automated Unit & Adversarial Test Suite
│
└── static/
    ├── css/
    │   └── style.css           # Modern glassmorphic dark theme dashboard UI
    ├── js/
    │   └── app.js              # Web Speech API & Interactive UI controller
    └── index.html              # Interactive Voice Agent Sandbox Dashboard
```

---

## 5. System Prompt & Dynamic Variables

The System Prompt is defined in [`prompts/system_prompt.py`](file:///d:/Assignment/prompts/system_prompt.py) and dynamically injects:
- `{{company_name}}`: Home Credit
- `{{agent_name}}`: Priya
- `{{agent_gender}}`: Female
- `{{customer_name}}`: Customer Name
- `{{language_to_speak}}`: English / Hinglish
- `{{additional_context_from_rag}}`: RAG context snippets
- `{{current_date}}`, `{{current_day}}`, `{{current_time}}`
- `{{conversation_history}}`, `{{customer_utterance}}`

---

## 6. Retell AI / Bolna Voice Platform Integration

The server provides a native Retell AI / Bolna compliant webhook endpoint at `/api/retell-webhook`.

### Webhook URL
`POST https://your-server-domain.com/api/retell-webhook`

### Payload Sample (Retell AI Webhook Request)
```json
{
  "event": "user_utterance",
  "call": {
    "call_id": "call_9876543210"
  },
  "args": {
    "transcript": "I have a residential house in Delhi."
  }
}
```

### Server Response Payload
```json
{
  "response_type": "text",
  "content": "Is the property solely owned by you, or is it under joint ownership?",
  "end_call": false
}
```

---

## 7. Setup & Local Installation

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### Installation Steps

1. **Clone or Navigate to Project Directory**:
   ```bash
   cd d:/Assignment
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Application Server**:
   ```bash
   python app.py
   ```
   Or via Uvicorn directly:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access Web Dashboard**:
   Open browser at `http://localhost:8000`

---

## 8. Interactive Web Dashboard & Voice Sandbox

The interactive dashboard at `http://localhost:8000` features:
- **Live 7-Point Eligibility Checklist**: Updates in real-time as entities are extracted.
- **Voice Input & Speech Output (STT/TTS)**: Talk to the agent using your browser microphone!
- **Quick Test Scenarios**: Click preset chips to test agricultural rejections, balance transfers, busy callbacks, and out-of-order inputs.
- **RAG Inspector**: View live retrieved product knowledge sections.
- **Automated Test Matrix Runner**: One-click execution of the entire 16-test suite directly from the UI header!

---

## 9. Test Matrix Suite (16 Scenarios)

Run the full automated test suite via CLI:

```bash
python -m unittest tests/test_matrix.py
```

### Test Results Matrix

| Test ID | Scenario Description | Input Sample | Expected Outcome | Result |
|---|---|---|---|---|
| **1** | Fully Eligible Customer | 7-step complete response | Handoff to Senior Expert | **PASS** |
| **2** | Agricultural Property | "I have an agricultural farmland" | Immediate Disqualification | **PASS** |
| **3** | Cash Income | "I get income in cash" | Immediate Disqualification | **PASS** |
| **4** | Missing Original Documents | "I don't have original documents" | Immediate Disqualification | **PASS** |
| **5** | Tenure Below Minimum (2 yrs) | "I want 2 years tenure" | Disqualification (< 3 yrs) | **PASS** |
| **6** | Tenure Above Maximum (20 yrs) | "I want 20 years tenure" | Disqualification (> 15 yrs) | **PASS** |
| **7** | Loan Amount > ₹75 Lakh | "I need ₹90 lakh loan" | Negotiates ₹75 Lakh Cap | **PASS** |
| **8** | Joint Ownership | "It is joint property" | Eligible (Continues) | **PASS** |
| **9** | Existing Property Loan | "I already have a loan on this" | Transfer Specialist | **PASS** |
| **10** | EMI Reduction Request | "I want to reduce my EMI" | Transfer Specialist | **PASS** |
| **11** | Customer Busy | "I am busy right now" | Callback Flow | **PASS** |
| **12** | Information Out of Order | "Value 1 Cr, need 50L for 12 yrs" | Remembers multi-fields | **PASS** |
| **13** | Contradiction (Adversarial) | "Residential... actually agricultural" | Latest answer -> Disqualify | **PASS** |
| **14** | Multiple Answers in 1 Sentence | 5 items in 1 utterance | Captures all 5 items | **PASS** |
| **15** | RAG Product Interruption | "What is the exact interest rate?" | RAG answer + return to flow | **PASS** |
| **16** | Ambiguous Documents Answer | "Papers probably somewhere" | Asks explicit clarification | **PASS** |

---

## 10. Submission Checklist

- [x] Complete System Prompt in `prompts/system_prompt.py`
- [x] State Management & Eligibility Engine in `agent/state.py` & `agent/eligibility.py`
- [x] RAG Module & Knowledge Base in `rag/rag_engine.py` & `rag/knowledge.txt`
- [x] Webhook integration for Retell AI / Bolna in `app.py` (`/api/retell-webhook`)
- [x] Interactive Web UI Sandbox Dashboard in `static/index.html`
- [x] 16 Automated Test Scenarios passing in `tests/test_matrix.py`
- [x] Comprehensive `README.md`
#   A s s i g n m e n t  
 
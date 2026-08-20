# HealthAI v0.2 — Intelligent Follow-Up Assessment

> **Milestone 2 Deliverable — College Minor Project**  
> An AI-powered healthcare guidance and symptom assessment chatbot featuring intelligent follow-up questions, multi-turn conversation context, structured AI responses, and emergency prioritization.

---

## 📌 Project Overview

**HealthAI** is an AI-powered healthcare guidance and symptom assessment assistant. It is designed to evaluate user health inquiries interactively, recognize when essential clinical details are missing, and ask 3–5 targeted follow-up questions before providing evidence-based healthcare information.

> [!IMPORTANT]
> **HealthAI Role & Scope**:  
> HealthAI provides educational **symptom assessment** and healthcare guidance, **not medical diagnosis**. It never claims to be a doctor, never makes definitive diagnoses, and never prescribes medications or dosages. In acute or life-threatening situations, it immediately prioritizes emergency instructions.

---

## 🚀 What's New in v0.2

1. 🧠 **Intelligent Follow-Up Questions**: Automatically detects when user input lacks critical information (duration, location, severity 1–10, associated symptoms, triggers) and asks 3–5 targeted follow-up questions.
2. 💬 **Multi-Turn Conversation Context**: Retains session history in memory so users can answer questions naturally (e.g., referring to "it") without repeating themselves.
3. 📋 **Structured JSON AI Responses**: Guarantees predictable outputs using Pydantic v2 schemas (`response_type`, `message`, `questions`, `risk_hint`).
4. 🚨 **Emergency Prioritization**: Immediately detects red-flag symptoms and provides concise emergency guidance without asking unnecessary follow-up questions.
5. 🛡️ **Prevents Repeated Questions**: Remembers information the user has already provided in previous turns and stops questioning once sufficient details are gathered.
6. 🗄️ **Temporary In-Memory Storage**: Context is stored in memory via `ConversationService` (designed to be replaced with **MongoDB** in Milestone 3).

---

## 📂 Project Structure

```
HealthAI/
├── backend/
│   ├── __init__.py                 # Backend package initializer
│   ├── main.py                     # FastAPI application entry point, CORS, static mounting
│   ├── config.py                   # Environment settings & dynamic reload (GEMINI_API_KEY, GEMINI_MODEL)
│   │
│   ├── models/
│   │   ├── __init__.py             # Models package initializer
│   │   └── chat_models.py          # Pydantic v2 schemas (ChatRequest, ChatResponse, StructuredAiOutput)
│   │
│   ├── routes/
│   │   ├── __init__.py             # Routes package initializer
│   │   └── chat.py                 # POST /api/chat route with conversation_id support
│   │
│   ├── services/
│   │   ├── __init__.py             # Services package initializer
│   │   ├── gemini_service.py       # Structured Gemini API client wrapper with fallback
│   │   └── conversation_service.py # In-memory session manager with sliding window buffer
│   │
│   └── prompts/
│       ├── __init__.py             # Prompts package initializer
│       └── system_prompt.py        # Safety-focused healthcare system prompt & JSON schema rules
│
├── frontend/
│   ├── index.html                  # Healthcare chatbot web interface with follow-up UI
│   ├── style.css                   # Modern healthcare design system & responsive styling
│   └── script.js                   # Chat UI logic, session tracking, follow-up rendering, markdown
│
├── .env                            # Environment variables (excluded from git)
├── .env.example                    # Template for environment configuration
├── .gitignore                      # Git ignore rules (.env, __pycache__, virtualenvs)
├── requirements.txt                # Python package dependencies
└── README.md                       # Project documentation
```

---

## 🔄 Intelligent Assessment Workflow

```
User Message
     │
     ▼
Safety Check
     │
     ├─────────────── Red Flag ───────────────┐
     │                                        │
     ▼                                        ▼
No immediate red flag                 Emergency Guidance
     │                             (No follow-up questions)
     ▼
Information Sufficiency Check
     │
     ├───────────────┬───────────────┐
     │               │               │
     ▼               ▼               ▼
Need info        Enough info     Unclear
     │               │               │
     ▼               ▼               ▼
Follow-up        General         Ask targeted
questions        guidance        clarification
(max 5)          (questions=[])  
     │
     ▼
User answers in chat
     │
     ▼
Context retained in session (conv_...)
     │
     ▼
Re-evaluate & provide guidance
```

---

## 📡 API Specification (`POST /api/chat`)

### 1. Request Format
```json
{
  "message": "I have stomach pain.",
  "conversation_id": "conv_a1b2c3d4e5f6"
}
```
*(If `conversation_id` is omitted, the backend generates a new session ID.)*

### 2. Follow-Up Response (`response_type: "follow_up"`)
```json
{
  "conversation_id": "conv_a1b2c3d4e5f6",
  "response_type": "follow_up",
  "message": "I'd like to understand your symptoms a little better to provide helpful information.",
  "questions": [
    "Where in your stomach is the pain located (e.g. upper, lower right)?",
    "When did the pain start and did it come on suddenly?",
    "How severe is it on a scale from 1 to 10?",
    "Do you have fever, nausea, vomiting, or changes in bowel habits?"
  ],
  "risk_hint": "unknown"
}
```

### 3. General Guidance Response (`response_type: "guidance"`)
```json
{
  "conversation_id": "conv_a1b2c3d4e5f6",
  "response_type": "guidance",
  "message": "Based on the details you provided...",
  "questions": [],
  "risk_hint": "low"
}
```

### 4. Emergency Response (`response_type: "emergency"`)
```json
{
  "conversation_id": "conv_a1b2c3d4e5f6",
  "response_type": "emergency",
  "message": "These symptoms may indicate a medical emergency. Please contact your local emergency services or seek immediate urgent medical care.",
  "questions": [],
  "risk_hint": "emergency"
}
```

---

## 🛠️ Installation & Execution

### 1. Prerequisites
- Python 3.10 or higher installed
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Ensure `.env` contains your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
HOST=127.0.0.1
PORT=8000
```

### 4. Run the Application
```bash
python -m uvicorn backend.main:app --reload
```

### 5. Access the Web App
Open your browser and navigate to:
- **Web App**: [http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend Status Healthcheck**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🧪 Testing Scenarios

Run the automated test suite covering all 7 milestone scenarios:
```bash
python scratch/test_v02.py
```

| Scenario | Input | Expected Output |
| :--- | :--- | :--- |
| **Test 1: Insufficient Info** | `"I have a headache."` | `response_type: "follow_up"` with 3–5 targeted questions |
| **Test 2: Sufficient Info Upfront** | Detailed headache description | `response_type: "guidance"` without follow-up questions |
| **Test 3: Context Retention** | Turn 1: `"Headache"` $\rightarrow$ Turn 2: `"Mild 3/10 since yesterday"` | AI understands context and transitions to guidance |
| **Test 4: Emergency Priority** | `"Sudden crushing chest pain & difficulty breathing"` | `response_type: "emergency"`, urgent care advice, 0 questions |
| **Test 5: Avoid Repeated Questions** | User provides onset $\rightarrow$ AI never re-asks onset | Avoids redundant questioning |
| **Test 6: Safe API Failure** | Simulated external API error | Returns `503` without exposing API keys or stack traces |
| **Test 7: Empty Input Validation** | Empty or whitespace string | Backend rejects with `422 Unprocessable Entity` |

---

## 🔮 Future Milestone Roadmap (Milestone 3)

The architecture is prepared for next-stage enhancements:
- 🗄️ **Persistent Database**: Replace `ConversationService` in-memory dictionary with **MongoDB** collections for persistent chat history across sessions.
- 👤 **User Authentication & Profiles**: JWT-based login with optional user health profiles (allergies, chronic conditions).
- 📊 **ML Risk Triage Classifier**: Machine learning classification pipeline for automated severity scoring before LLM generation.

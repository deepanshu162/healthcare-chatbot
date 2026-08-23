# HealthAI v0.3 — Intelligent Follow-Up Assessment & MongoDB Persistence

> **Milestone 3 Deliverable — College Minor Project**  
> An AI-powered healthcare guidance and symptom assessment platform featuring MongoDB cloud persistence, JWT user authentication, intelligent MCQ follow-up questions, multi-turn conversation memory, structured AI responses, and emergency prioritization.

---

## 📌 Project Overview

**HealthAI** is an AI-powered healthcare guidance and symptom assessment assistant. It evaluates user health inquiries interactively, recognizes when essential clinical details are missing, asks 3–5 targeted follow-up questions with multiple-choice answers, and securely saves assessment histories to **MongoDB** across devices.

> [!IMPORTANT]
> **HealthAI Role & Scope**:  
> HealthAI provides educational **symptom assessment** and healthcare guidance, **not medical diagnosis**. It never claims to be a doctor, never makes definitive diagnoses, and never prescribes medications or dosages. In acute or life-threatening situations, it immediately prioritizes emergency instructions.

---

## 🚀 What's New in v0.3

1. 🗄️ **Persistent MongoDB Storage**: Full database integration with `motor` (async driver) and `pymongo`, compatible with **MongoDB Atlas** (cloud) and local MongoDB.
2. 👤 **JWT User Authentication**: Secure registration, login, bcrypt password hashing, and user profile management (`/api/auth/register`, `/api/auth/login`, `/api/auth/me`).
3. 📜 **Assessment History Sidebar**: Collapsible history drawer with real-time session listing, risk severity badges (Emergency / High / Moderate / Low), "+ New Assessment" action, and conversation deletion.
4. 🧠 **Intelligent Follow-Up Questions**: Automatically detects when user input lacks critical details and presents 3–5 targeted MCQ answer options.
5. 💬 **Multi-Turn Context Retention**: Retains session history in MongoDB collections (`conversations`, `messages`) so users can continue previous assessments anytime.
6. 🚨 **Emergency Prioritization**: Immediately detects red-flag symptoms and provides urgent medical safety instructions without asking unnecessary questions.

---

## 📂 Project Structure

```
HealthAI/
├── backend/
│   ├── __init__.py                 # Backend package initializer
│   ├── main.py                     # FastAPI application entry point, CORS, lifespan
│   ├── config.py                   # Environment settings (Gemini, MongoDB, JWT)
│   │
│   ├── db/
│   │   ├── __init__.py             # DB package initializer
│   │   └── mongodb.py              # Async MongoDB client lifecycle, ping & index setup
│   │
│   ├── models/
│   │   ├── __init__.py             # Models package initializer
│   │   ├── chat_models.py          # Chat request/response schemas (Pydantic v2)
│   │   ├── user_models.py          # User auth schemas (Register, Login, Token, UserResponse)
│   │   └── conversation_models.py  # Conversation history schemas (Summary, Detail, Messages)
│   │
│   ├── routes/
│   │   ├── __init__.py             # Routes package initializer
│   │   ├── chat.py                 # POST /api/chat with persistence & optional user auth
│   │   ├── auth.py                 # POST /api/auth/register, /login, GET /me
│   │   └── conversations.py        # GET /api/conversations, GET/DELETE /api/conversations/{id}
│   │
│   ├── services/
│   │   ├── __init__.py             # Services package initializer
│   │   ├── auth_service.py         # Password hashing, JWT token creation/verification
│   │   ├── conversation_service.py # MongoDB session manager with sliding window cache
│   │   └── gemini_service.py       # Structured Gemini API client wrapper with fallback
│   │
│   └── prompts/
│       ├── __init__.py             # Prompts package initializer
│       └── system_prompt.py        # Healthcare safety system prompt & JSON schema rules
│
├── frontend/
│   ├── index.html                  # Web app layout with History Sidebar & Auth Modal
│   ├── style.css                   # Healthcare design system, sidebar drawer & responsive styling
│   └── script.js                   # Frontend logic: Auth tokens, chat, MCQ rendering, sidebar
│
├── .env                            # Environment variables (excluded from git)
├── .env.example                    # Template for environment configuration
├── .gitignore                      # Git ignore rules (.env, __pycache__, virtualenvs)
├── requirements.txt                # Python package dependencies
├── vercel.json                     # Vercel deployment configuration
└── README.md                       # Project documentation
```

---

## 📡 API Specification

### Authentication Endpoints
- `POST /api/auth/register`: Register user with name, email, and password.
- `POST /api/auth/login`: Authenticate user and receive JWT bearer token.
- `GET /api/auth/me`: Get current user profile (requires `Authorization: Bearer <token>`).

### Conversation Endpoints
- `GET /api/conversations`: List all conversation summaries for current user.
- `GET /api/conversations/{conversation_id}`: Retrieve all messages, MCQ options, and risk triage records.
- `DELETE /api/conversations/{conversation_id}`: Delete a specific assessment session.
- `DELETE /api/conversations`: Clear all sessions for authenticated user.

### Chat Endpoint (`POST /api/chat`)
```json
{
  "message": "I have stomach pain.",
  "conversation_id": "conv_a1b2c3d4e5f6"
}
```

---

## 🛠️ Installation & Execution

### 1. Prerequisites
- Python 3.10 or higher
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))
- MongoDB Atlas URI or Local MongoDB instance

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create or update your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
HOST=127.0.0.1
PORT=8000

# MongoDB Configuration (Local or MongoDB Atlas)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=healthai

# Authentication Secret
JWT_SECRET_KEY=your_secure_random_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 4. Run the Application
```bash
python -m uvicorn backend.main:app --reload
```

### 5. Access the Web App
Open your browser and navigate to:
- **Interactive Web App**: [http://127.0.0.1:8000/frontend/index.html](http://127.0.0.1:8000/frontend/index.html) (or open `frontend/index.html` directly)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend & Database Healthcheck**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Automated Testing

Run the test suite verifying MongoDB persistence, authentication, and chat flows:
```bash
python scratch/test_db_and_auth.py
```

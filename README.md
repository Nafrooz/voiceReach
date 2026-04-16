# VoiceReach — Voice AI for Accessibility

## 100% Free Stack: Vapi + Qdrant + Groq (LLaMA 3.3 70B)

## Live Demo
URL: https://your-app.railway.app/demo

## Run Locally (Detailed)

### Prerequisites
- **Node.js**: 18+ recommended (for the React/Vite frontend)
- **Python**: 3.11 (backend)
- **Docker**: optional, but recommended for running the backend quickly
- **Qdrant Cloud**: free tier URL + API key (this project uses **Qdrant Cloud**, not a local Qdrant container)
- **Groq API key**: free tier key for LLaMA models

### Environment variables

#### Backend `.env`
Copy the example and fill in real values:

```bash
cp .env.example .env
```

Required:
- **`QDRANT_URL`**: your Qdrant Cloud URL (example: `https://xxxx.qdrant.io:6333`)
- **`QDRANT_API_KEY`**: your Qdrant Cloud API key
- **`GROQ_API_KEY`**: your Groq API key (starts with `gsk_...`)
- **`VAPI_SECRET`**: your Vapi webhook secret (used for HMAC signature validation)

#### Frontend env (optional)
The frontend works out of the box with the backend on `http://localhost:8000`. You can override via a Vite env file:

Create `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000
VITE_VAPI_PUBLIC_KEY=your_vapi_public_key
VITE_VAPI_ASSISTANT_ID=your_vapi_assistant_id
```

Notes:
- **`VITE_API_URL`** can be either `http://localhost:8000` or `http://localhost:8000/api/v1` (the app normalizes it).
- **`VITE_VAPI_*`** values are only needed to enable the **browser microphone** button on `/demo`.

### Start the backend

#### Option A (recommended): Docker Compose
From repo root:

```bash
docker compose up --build
```

Backend will be available at:
- **Health**: `http://localhost:8000/health`
- **API base**: `http://localhost:8000/api/v1`

#### Option B: Python virtualenv (no Docker)
From repo root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run that command inside the backend package directory:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start the frontend
In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:
- **Demo UI**: `http://localhost:5173/demo`

### Seed the knowledge base (recommended before demo)
Once the backend is running:

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/seed"
```

Expected response shape:
- `{"total_chunks_ingested": <number>, "documents_processed": <number>}`

### Quick verification checklist
- **Backend health**:

```bash
curl "http://localhost:8000/health"
```

- **Frontend talking to backend**:
  - Open `http://localhost:5173/demo`
  - Type a question like: “What is Ayushman Bharat? Am I eligible?”
  - You should see a response, plus retrieved chunks in the left panel after seeding.

### Common issues
- **Frontend shows network errors**:
  - Confirm backend is running on `http://localhost:8000`
  - If you changed ports, set `VITE_API_URL` in `frontend/.env.local` and restart `npm run dev`
- **Seeding fails**:
  - Re-check `QDRANT_URL` / `QDRANT_API_KEY` in `.env`
  - Confirm your Qdrant Cloud instance is reachable
- **Mic button disabled on `/demo`**:
  - Set `VITE_VAPI_PUBLIC_KEY` and `VITE_VAPI_ASSISTANT_ID` in `frontend/.env.local`

## 60-Second Demo Script for Judges
1. Open /demo page
2. Click mic → say: "What is Ayushman Bharat? Am I eligible?"
3. Agent responds in 2-3 seconds with eligibility criteria (in English)
4. Say: "Mujhe apply kaise karna hai?" (How do I apply? — Hindi)
5. Agent responds IN HINDI with application steps
6. Point to the left panel: "Look — these are the exact chunks retrieved from Qdrant"
7. Point to the right panel: "LLaMA 3.3 70B on Groq generated this in <300ms"

## Why This Stack Wins
- Vapi: Real-time voice, multilingual STT, function calling
- Qdrant: Semantic search over domain knowledge — finds relevant info, not just keywords
- Groq: Free, 500+ tok/sec, LLaMA 3.3 70B quality — voice responses feel instant

## Setup in 5 Minutes
1. git clone && cd voicereach
2. cp .env.example .env → fill QDRANT_URL, QDRANT_API_KEY, GROQ_API_KEY
3. docker compose up
4. curl -X POST localhost:8000/api/v1/ingest/seed
5. Open localhost:5173/demo

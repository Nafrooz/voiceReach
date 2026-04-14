# VoiceReach — Voice AI for Accessibility

## 100% Free Stack: Vapi + Qdrant + Groq (LLaMA 3.3 70B)

## Live Demo
URL: https://your-app.railway.app/demo

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
3. docker-compose up
4. curl -X POST localhost:8000/api/v1/ingest/seed
5. Open localhost:3000/demo

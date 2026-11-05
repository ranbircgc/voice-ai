# Saarthi — Free Local Hindi / English / Hinglish Voice AI

Saarthi runs AI inference on your own computer using Ollama. No paid API, API key, subscription, or cloud inference credits are required. Internet is only needed to download the model and optionally use web search.

## Features
- Hindi, English and Hinglish text chat
- Voice-note input using local Faster-Whisper
- Speech output using the operating system's built-in voices
- Stop-speaking control
- SQLite conversation history stored locally
- Optional DuckDuckGo web search (internet required)
- React + Vite frontend and FastAPI backend

## Recommended setup for Apple Silicon Mac with 16 GB RAM
Install Ollama from https://ollama.com/download, then open the Ollama app. In Terminal, download the model:

```bash
ollama pull qwen3:8b
```

This model runs locally. It uses your Mac's memory and compute; no Ollama Cloud account or API key is needed. If it feels too slow or uses too much memory, use `qwen3:4b` instead and set that model in `backend/.env`.

## Requirements
- Ollama installed and running locally
- Python 3.10–3.12 recommended (Python 3.11 suggested)
- Node.js 20.19+ or 22.12+
- 16 GB RAM recommended
- Browser microphone permission for voice input

## 1. Configure the backend

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The default configuration is:

```env
OLLAMA_MODE=local
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
WHISPER_MODEL=base
```

If you already created `backend/.env` while testing Ollama Cloud, edit that existing file and replace its Ollama settings with the local settings above. Remove the old cloud API key line. Never share or commit API keys.

Start the backend:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Check http://localhost:8000/api/health. It should report `"mode":"local"` and `"ollama_connected":true`.

## 2. Start the frontend

Open a second Terminal window:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Free operation and limitations
- Text AI inference: local and free; no per-request API charges.
- Speech recognition: local; the Whisper model downloads once.
- Speech output: macOS built-in `say` voices.
- Conversation memory: local SQLite database.
- Web search: optional, needs internet and uses DuckDuckGo's public search page.
- Hosting: local app is free to run. A public website still needs a separately reachable backend; free frontend hosting does not make remote AI inference free.

The Mac must remain on and Ollama running while Saarthi is in use. Electricity, internet access for optional search/downloads, and your computer's hardware are not included in the meaning of free.

## Voice limitations
Voice chat is turn-based, not full-duplex live conversation. The stop button interrupts current audio playback.

## Troubleshooting
- **Ollama not connected:** open the Ollama app, then run `ollama list`.
- **Model missing:** run `ollama pull qwen3:8b`.
- **Slow responses:** switch to `qwen3:4b` in `backend/.env`, then restart the backend.
- **Microphone blocked:** allow microphone access for localhost in browser settings.
- **Whisper install fails:** use Python 3.11 or 3.12 in a fresh virtual environment.

## Privacy
Chat prompts and responses are sent to the Ollama process on your own computer, not Ollama Cloud. Transcription, speech synthesis, and SQLite memory also run locally. If you enable Web search, your search query is sent to DuckDuckGo.

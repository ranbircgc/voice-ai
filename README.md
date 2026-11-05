# Saarthi — Local Hindi / English / Hinglish Voice AI

A local-first voice assistant for macOS, Windows and Linux. The LLM, speech recognition,
speech synthesis and conversation memory run on your computer. Internet search uses
DuckDuckGo's public HTML endpoint when you explicitly ask for current information.

## Features

- Text chat and voice-note chat
- Hindi, English and Hinglish prompts (model-dependent quality)
- Local Ollama model for responses
- Local Faster-Whisper speech-to-text
- Local system TTS (macOS `say`; Windows/Linux via `pyttsx3`)
- Multiple selectable system voices
- Stop-speaking button (interrupts current audio playback)
- SQLite conversation memory, with clear-memory control
- Optional DuckDuckGo web search tool
- React + Vite UI and FastAPI backend

**Current voice limitation:** this is turn-based voice chat, not a full-duplex phone-call agent.
The Stop button immediately interrupts speech playback; speak again after it stops.
True low-latency streaming barge-in needs a streaming STT/TTS stack and more integration.

## Requirements

- Python 3.10–3.12 recommended (Python 3.11 suggested)
- Node.js 20.19+ or 22.12+
- Ollama: https://ollama.com
- 8 GB RAM minimum; 16 GB recommended
- Microphone permission for your browser

## 1. Install Ollama and a model

Install Ollama, then run:

```bash
ollama pull qwen2.5:3b
```

If Ollama is already running as a desktop app, you do not need to run `ollama serve`.

## 2. Start the backend

From the repository root:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

On Windows, activate with ` .venv\Scripts\activate `.

The first voice request downloads the Whisper model (about 150 MB for `base`).
Set `WHISPER_MODEL=tiny` in `.env` for a smaller/faster download.

## 3. Start the website

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and allow microphone access.

## Configuration

Edit `backend/.env`:

```env
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
WHISPER_MODEL=base
```

On macOS, list installed voices with `say -v '?'`. On Windows/Linux, `pyttsx3`
uses voices installed on the operating system.

## Free deployment

The frontend can be deployed free on Cloudflare Pages, but the AI backend is intentionally
local and private. A deployed frontend needs a securely reachable backend URL to chat;
the default localhost backend only works on the same computer. Do not expose port 8000
directly to the public internet or put secrets in frontend code. For private remote access,
use a VPN such as Tailscale between your devices.

Cloudflare Pages settings:
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

## Troubleshooting

- **Ollama connection error:** open Ollama and run `ollama list`.
- **Model not found:** run `ollama pull qwen2.5:3b`.
- **Microphone blocked:** allow microphone access for localhost in browser settings and reload.
- **Whisper install fails:** use Python 3.11 or 3.12 in a fresh virtual environment.
- **No sound on macOS:** run `say "Hello"` in Terminal and check system output volume.

## Privacy

Audio is uploaded only to your local FastAPI server for transcription. The local Ollama
model and SQLite memory stay on your computer. If Web search is enabled, search terms
are sent to DuckDuckGo. This is not a zero-network application when web search is used.

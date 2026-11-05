# Saarthi — Local Hindi / English / Hinglish Voice AI

A voice assistant for macOS, Windows and Linux. AI responses use the high-capability
Ollama Cloud model by default; speech recognition, speech synthesis and conversation
memory run locally on your computer. Internet search uses DuckDuckGo's public HTML
endpoint when you explicitly ask for current information.

## Features

- Text chat and voice-note chat
- Hindi, English and Hinglish prompts (model-dependent quality)
- Ollama Cloud model for responses (default: kimi-k3.1-pro)
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
- Ollama account and an API key for Cloud inference (usage may require an eligible plan or credits)

## 1. Configure Ollama Cloud

Create an API key in your Ollama account, then copy the example environment file:

```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and replace the placeholder with your real key:

```env
OLLAMA_MODE=cloud
OLLAMA_API_KEY=your_real_ollama_api_key
OLLAMA_MODEL=kimi-k3.1-pro
```

The key stays on your backend and must never be placed in frontend code or committed
to GitHub. The default model is a high-capability cloud model; cloud usage may require
an eligible Ollama plan or purchased usage credits. No model download is required.

To use a different model, set `OLLAMA_MODEL` to a model name listed by Ollama's
cloud model catalog. To switch back to local inference, set `OLLAMA_MODE=local`.

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

Edit `backend/.env` to change the cloud model or speech-recognition size.
Keep `OLLAMA_API_KEY` private.

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

- **Ollama Cloud key missing:** add your key to `backend/.env`, then restart the backend.
- **401 error:** create or copy a valid Ollama API key.
- **402 error:** check your Ollama plan or add usage credits.
- **Model not found:** verify the model name in Ollama's cloud catalog.
- **Microphone blocked:** allow microphone access for localhost in browser settings and reload.
- **Whisper install fails:** use Python 3.11 or 3.12 in a fresh virtual environment.
- **No sound on macOS:** run `say "Hello"` in Terminal and check system output volume.

## Privacy

Audio is uploaded only to your local FastAPI server for transcription. SQLite memory and speech processing stay on your computer. Chat prompts and responses
are sent to Ollama Cloud for inference. If Web search is enabled, search terms
are sent to DuckDuckGo. This is not a zero-network application when web search is used.

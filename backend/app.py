import os
import platform
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()
BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
DB = DATA / "chat.db"
OLLAMA_MODE = os.getenv("OLLAMA_MODE", "cloud").strip().lower()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "kimi-k3.1-pro").strip()
OLLAMA_CLOUD_CHAT_URL = "https://ollama.com/api/chat"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

app = FastAPI(title="Saarthi Local Voice AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """You are Saarthi, a helpful voice-first assistant.
Reply naturally in the language used by the user: Hindi, English, or Hinglish.
Keep spoken answers concise unless the user asks for detail. Never claim to have
searched the web unless search results were supplied. Use conversation context
when relevant. If you do not know something, say so clearly."""


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")


init_db()


class ChatRequest(BaseModel):
    message: str
    web_search: bool = False


class SpeakRequest(BaseModel):
    text: str
    voice: str = "default"
    rate: int = 175


def history(limit=16):
    with db() as con:
        rows = con.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def save(role, content):
    with db() as con:
        con.execute("INSERT INTO messages(role, content) VALUES (?, ?)", (role, content))


def search_web(query: str):
    try:
        url = "https://html.duckduckgo.com/html/?q=" + quote(query)
        response = requests.get(
            url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for item in soup.select(".result")[:5]:
            title = item.select_one(".result__title")
            snippet = item.select_one(".result__snippet")
            link = title.find("a") if title else None
            if link:
                results.append({
                    "title": link.get_text(" ", strip=True),
                    "url": link.get("href", ""),
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                })
        return results
    except Exception as exc:
        return [{"title": "Search unavailable", "url": "", "snippet": str(exc)}]


def ollama_headers():
    if OLLAMA_MODE == "cloud":
        if not OLLAMA_API_KEY:
            raise HTTPException(503, "Add your OLLAMA_API_KEY to backend/.env to use Ollama Cloud.")
        return {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
    return {}


@app.get("/api/health")
def health():
    if OLLAMA_MODE == "cloud" and not OLLAMA_API_KEY:
        return {"status": "needs_setup", "ollama_connected": False, "mode": "cloud",
                "model": OLLAMA_MODEL, "message": "Add OLLAMA_API_KEY to backend/.env"}
    try:
        if OLLAMA_MODE == "cloud":
            response = requests.get("https://ollama.com/api/tags", headers=ollama_headers(), timeout=12)
        else:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        ollama_ok = response.ok
    except Exception:
        ollama_ok = False
    return {"status": "ok" if ollama_ok else "offline", "ollama_connected": ollama_ok,
            "mode": OLLAMA_MODE, "model": OLLAMA_MODEL}


@app.get("/api/voices")
def voices():
    if platform.system() == "Darwin":
        try:
            output = subprocess.check_output(["say", "-v", "?"], text=True, timeout=5)
            names = []
            for line in output.splitlines():
                match = re.match(r"^(\S+)\s+", line)
                if match:
                    names.append(match.group(1))
            return {"voices": ["default"] + sorted(set(names))}
        except Exception:
            pass
    try:
        import pyttsx3
        engine = pyttsx3.init()
        result = ["default"] + [voice.id for voice in engine.getProperty("voices")]
        engine.stop()
        return {"voices": result}
    except Exception:
        return {"voices": ["default"]}


@app.post("/api/chat")
def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(400, "Message is empty")
    web_results = search_web(message) if req.web_search else []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history())
    user_content = message
    if web_results:
        user_content += "\n\nWeb search results (use these, cite URLs in answer):\n" + "\n".join(
            f"- {item['title']}: {item['snippet']} ({item['url']})"
            for item in web_results
        )
    messages.append({"role": "user", "content": user_content})
    try:
        if OLLAMA_MODE == "cloud":
            if not OLLAMA_API_KEY:
                raise HTTPException(503, "Add your OLLAMA_API_KEY to backend/.env to use Ollama Cloud.")
            chat_url = OLLAMA_CLOUD_CHAT_URL
            headers = {**ollama_headers(), "Content-Type": "application/json"}
            timeout = 300
        else:
            chat_url = f"{OLLAMA_URL}/api/chat"
            headers = {"Content-Type": "application/json"}
            timeout = 180
        response = requests.post(
            chat_url,
            headers=headers,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
            timeout=timeout,
        )
        if response.status_code == 401:
            raise HTTPException(401, "Ollama Cloud rejected the API key. Check OLLAMA_API_KEY in backend/.env.")
        if response.status_code == 402:
            raise HTTPException(402, "This Ollama Cloud model requires an eligible plan or usage credits.")
        if response.status_code == 404:
            raise HTTPException(404, f"Model '{OLLAMA_MODEL}' was not found. Check the model name in backend/.env.")
        response.raise_for_status()
        answer = response.json()["message"]["content"].strip()
    except HTTPException:
        raise
    except requests.exceptions.ConnectionError:
        raise HTTPException(503, "Could not connect to Ollama. Check your internet connection.")
    except requests.exceptions.Timeout:
        raise HTTPException(504, "Ollama Cloud took too long to respond. Please retry.")
    except Exception as exc:
        raise HTTPException(502, f"Model error: {exc}")
    save("user", message)
    save("assistant", answer)
    return {"reply": answer, "sources": web_results}


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), language: Optional[str] = Form(None)):
    try:
        from faster_whisper import WhisperModel
        global whisper_model
        if "whisper_model" not in globals():
            whisper_model = WhisperModel(
                WHISPER_MODEL, device="cpu", compute_type="int8"
            )
        suffix = Path(audio.filename or "voice.webm").suffix or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
            temp.write(await audio.read())
            temp_path = temp.name
        try:
            segments, info = whisper_model.transcribe(
                temp_path,
                language=language if language not in ("auto", "", None) else None,
                vad_filter=True,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return {"text": text, "language": info.language}
        finally:
            os.unlink(temp_path)
    except Exception as exc:
        raise HTTPException(500, f"Transcription failed: {exc}")


@app.post("/api/speak")
def speak(req: SpeakRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Text is empty")
    # A unique output filename avoids simultaneous requests overwriting one another.
    import uuid
    output = DATA / f"speech-{uuid.uuid4().hex}.wav"
    try:
        if platform.system() == "Darwin":
            command = ["say", "-o", str(output), "--data-format=LEI16@22050"]
            if req.voice and req.voice != "default":
                command += ["-v", req.voice]
            command += ["-r", str(max(100, min(req.rate, 300))), text]
            subprocess.run(command, check=True, timeout=90, capture_output=True)
        else:
            import pyttsx3
            engine = pyttsx3.init()
            if req.voice and req.voice != "default":
                try:
                    engine.setProperty("voice", req.voice)
                except Exception:
                    pass
            engine.setProperty("rate", max(100, min(req.rate, 300)))
            engine.save_to_file(text, str(output))
            engine.runAndWait()
            engine.stop()
        if not output.exists():
            raise RuntimeError("Speech engine did not create audio")
        return FileResponse(
            output, media_type="audio/wav", filename="saarthi.wav",
            background=None,
        )
    except Exception as exc:
        raise HTTPException(500, f"Speech synthesis failed: {exc}")


@app.get("/api/history")
def get_history():
    return {"messages": history(100)}


@app.delete("/api/history")
def clear_history():
    with db() as con:
        con.execute("DELETE FROM messages")
    return {"ok": True}

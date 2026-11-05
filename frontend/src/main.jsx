import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Mic, Square, Send, Trash2, Globe, Bot, User, AudioLines, Radio } from 'lucide-react'
import './style.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [recording, setRecording] = useState(false)
  const [busy, setBusy] = useState(false)
  const [web, setWeb] = useState(false)
  const [voices, setVoices] = useState(['default'])
  const [voice, setVoice] = useState('default')
  const [health, setHealth] = useState(null)
  const [error, setError] = useState('')
  const [speaking, setSpeaking] = useState(false)
  const recorder = useRef(null)
  const chunks = useRef([])
  const audioRef = useRef(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(() => setHealth({ status: 'offline' }))
    fetch('/api/voices').then(r => r.json()).then(d => setVoices(d.voices || ['default'])).catch(() => {})
    fetch('/api/history').then(r => r.json()).then(d => setMessages(d.messages || [])).catch(() => {})
  }, [])

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, busy])

  async function sendMessage(text = input) {
    const value = text.trim()
    if (!value || busy) return
    setInput('')
    setError('')
    setMessages(prev => [...prev, { role: 'user', content: value }])
    setBusy(true)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: value, web_search: web })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Request failed')
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply, sources: data.sources || [] }])
      speak(data.reply)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function speak(text) {
    try {
      const res = await fetch('/api/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice })
      })
      if (!res.ok) throw new Error('Speech generation failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = url
        audioRef.current.onended = () => {
          setSpeaking(false)
          URL.revokeObjectURL(url)
        }
        await audioRef.current.play()
        setSpeaking(true)
      }
    } catch (e) {
      setError(e.message)
    }
  }

  function stopSpeaking() {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
    setSpeaking(false)
  }

  async function startRecording() {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : ''
      const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined)
      recorder.current = mr
      chunks.current = []
      mr.ondataavailable = e => {
        if (e.data.size) chunks.current.push(e.data)
      }
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(chunks.current, { type: mr.mimeType || 'audio/webm' })
        if (!blob.size) return
        const form = new FormData()
        form.append('audio', blob, 'voice.webm')
        form.append('language', 'auto')
        setBusy(true)
        try {
          const res = await fetch('/api/transcribe', { method: 'POST', body: form })
          const data = await res.json()
          if (!res.ok) throw new Error(data.detail || 'Transcription failed')
          if (data.text) await sendAfterTranscription(data.text)
          else setError('No speech detected. Try again.')
        } catch (e) {
          setError(e.message)
        } finally {
          setBusy(false)
        }
      }
      mr.start()
      setRecording(true)
    } catch (e) {
      setError('Microphone access failed. Allow microphone access for localhost and reload.')
    }
  }

  async function sendAfterTranscription(text) {
    setMessages(prev => [...prev, { role: 'user', content: text }])
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, web_search: web })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Request failed')
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply, sources: data.sources || [] }])
      speak(data.reply)
    } catch (e) {
      setError(e.message)
    }
  }

  function stopRecording() {
    if (recorder.current && recorder.current.state !== 'inactive') recorder.current.stop()
    setRecording(false)
  }

  async function clearMemory() {
    if (!confirm('Delete all saved conversation memory?')) return
    await fetch('/api/history', { method: 'DELETE' })
    setMessages([])
    setError('')
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon"><AudioLines size={22} /></div><div><b>SAARTHI</b><small>OLLAMA CLOUD AI</small></div></div>
      <div className="side-label">YOUR ASSISTANT</div>
      <div className="side-active"><Bot size={17} /> New conversation</div>
      <div className="side-note">Cloud-powered intelligence.<br />Speech and memory stay local.</div>
      <div className="sidebar-bottom">
        <div className="status"><span className={health?.ollama_connected ? 'dot online' : 'dot'}></span>{health?.ollama_connected ? 'Ollama Cloud connected' : 'Ollama Cloud not connected'}</div>
        <button className="clear-btn" onClick={clearMemory}><Trash2 size={15} /> Clear memory</button>
      </div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div><span className="eyebrow">PERSONAL AI COMPANION</span><h1>Talk to Saarthi</h1></div>
        <div className="top-actions">
          <label className="search-toggle"><input type="checkbox" checked={web} onChange={e => setWeb(e.target.checked)} /><Globe size={15} /> Web search</label>
          <select aria-label="Voice" value={voice} onChange={e => setVoice(e.target.value)}>
            {voices.map(v => <option key={v} value={v}>{v === 'default' ? 'Default voice' : v}</option>)}
          </select>
        </div>
      </header>

      <section className="chat-area">
        {messages.length === 0 ? <div className="welcome">
          <div className="orb"><AudioLines size={38} /></div>
          <span className="eyebrow">READY WHEN YOU ARE</span>
          <h2>Namaste. What’s on<br />your mind today?</h2>
          <p>Speak in Hindi, English, or Hinglish.<br />Powered by Ollama Cloud.</p>
          <div className="suggestions">
            {['Explain machine learning simply', 'Aaj ka din productive kaise banau?', 'Help me brainstorm an idea'].map(x => <button key={x} onClick={() => sendMessage(x)}>{x}</button>)}
          </div>
        </div> : <div className="messages">
          {messages.map((m, i) => <div className={'message ' + m.role} key={i}>
            <div className="avatar">{m.role === 'user' ? <User size={16} /> : <Bot size={16} />}</div>
            <div className="bubble"><div className="message-label">{m.role === 'user' ? 'YOU' : 'SAARTHI'}</div><div className="message-text">{m.content}</div>
              {m.sources?.length > 0 && <div className="sources"><b>Search sources</b>{m.sources.map((s, j) => <a key={j} href={s.url} target="_blank" rel="noreferrer">{s.title}</a>)}</div>}
            </div>
          </div>)}
          {busy && <div className="typing"><span></span><span></span><span></span> Saarthi is thinking…</div>}
          <div ref={bottomRef} />
        </div>}
      </section>

      {error && <div className="error">{error}</div>}
      <section className="composer-wrap">
        <div className="voice-status">{recording ? <><span className="recording-dot"></span> Listening… click stop when finished</> : speaking ? 'Saarthi is speaking' : 'Type or use your voice'}</div>
        <div className="composer">
          <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }} placeholder="Write a message… (Enter to send)" rows="1" />
          <div className="composer-actions">
            {speaking && <button className="stop-btn" title="Interrupt speech" onClick={stopSpeaking}><Square size={16} /></button>}
            {recording ? <button className="record-btn active" title="Stop recording" onClick={stopRecording}><Square size={17} /></button> : <button className="record-btn" title="Record voice" onClick={startRecording} disabled={busy}><Mic size={18} /></button>}
            <button className="send-btn" title="Send message" onClick={() => sendMessage()} disabled={!input.trim() || busy}><Send size={17} /></button>
          </div>
        </div>
        <div className="disclaimer"><Radio size={12} /> Ollama Cloud AI · Local speech recognition · Memory stored on this device</div>
      </section>
      <audio ref={audioRef} />
    </main>
  </div>
}

createRoot(document.getElementById('root')).render(<App />)

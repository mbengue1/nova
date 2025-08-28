
# N.O.V.A - No Ordinary Voice Assistant
# Hey Nova – Personal AI Assistant (MVP Stage)


## 📖 Overview

**Hey Nova** is a personal AI assistant inspired by J.A.R.V.I.S. and F.R.I.D.A.Y. from *Iron Man*. Unlike Siri or Alexa, Nova is designed for **deep integration, natural conversation, and proactive assistance**.

This project begins with a **MacBook MVP**: an always-listening assistant that responds to the wake word **“Hey Nova”**, understands your speech, routes commands to skills (like checking Notion or opening apps), and speaks back naturally using configurable voices.

Future stages will expand to Windows, iPhone, and cross-device operation, with proactive greetings, memory, and encrypted always-on operation.

---

## 🎯 MVP Goals

* Respond to **wake word**: "Hey Nova"
* Capture speech, transcribe with **Whisper**
* Route to **skills** (Notion, app control, math, system info)
* Fallback to **LLM (OpenAI API)** for natural conversation
* Speak back using **macOS TTS** (British, American, or custom neural voices)
* Support **barge-in capability** (interrupt Nova while speaking)
* Run in **Terminal** as a simple service

---

## 🛠️ Development Process

### Stage 1: Core Pipeline

1. **Wake Word Detection**

   * Tool: [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/)
   * Detects “Hey Nova” with low CPU usage
   * Alternative: Push-to-talk hotkey

2. **Audio Capture & STT**

   * Library: [faster-whisper](https://github.com/guillaumekln/faster-whisper) (local, efficient Whisper)
   * Captures audio, transcribes speech → text

3. **Brain / Router**

   * Router decides if input should go to:

     * **Skill** (e.g., open app, Notion lookup, adjust brightness)
     * **LLM (OpenAI GPT)** for conversation
   * Ensures replies are dynamic, not scripted

4. **TTS (Speech Output) & Interruption**

   * Default: macOS `AVSpeechSynthesizer` or `say` command (built-in voices)
   * Configurable for British/futuristic tones
   * Future: upgrade to **Azure Neural TTS** / **ElevenLabs**

5. **Skills (Capabilities)**

   * Small Python modules, each with `match()` + `run()`
   * Examples:

     * `app_control.open_app("vscode")`
     * `notion.today_agenda()`
     * `sysinfo.current_time()`
   * Output is **context**, which LLM phrases naturally

---

### Stage 2: Proactive Behavior

* **Event Engine**: triggers on login, Wi-Fi connect, or time windows
* **Context Pack**: aggregates Notion, weather, deadlines, habits
* **LLM** generates greetings dynamically (e.g., “Good evening, Mouhamed. I see you have basketball at 8. Want me to set a reminder?”)

---

### Stage 3: Multi-Device Expansion

* Extract “brain” into a **FastAPI/WebSocket server**
* Mac, Windows, iPhone listeners → send audio/text to the API
* Each listener only handles **mic + speaker**; brain + skills stay centralized

---

## 🧰 Tools & Technologies

**Core MVP (✅ Implemented)**

* **Language:** Python 3.11+ with virtual environment
* **Wake word:** [Porcupine](https://picovoice.ai/) with custom "Hey Nova" model
* **STT:** Whisper (via [faster-whisper](https://github.com/guillaumekln/faster-whisper)) - local processing
* **Brain:** **LLM-first architecture** using OpenAI GPT-4o-mini for intelligent responses
* **TTS:** **Azure Neural TTS** (Libby voice) + macOS built-in voices fallback
* **Automation:** AppleScript/JXA for app & system control
* **Audio:** PyAudio with sounddevice for reliable audio processing
* **Architecture:** Modular design with clean separation of concerns

**Future**

* **TTS (Premium):** Azure Neural TTS, Amazon Polly, ElevenLabs
* **LLM (Offline):** LLaMA or GPT4All for private local inference
* **Server:** FastAPI for HTTP/WS API
* **Memory:** SQLite + vector DB for context recall
* **Packaging:** macOS LaunchAgent for autostart; Swift menubar app

---

## 🖥️ Development Flow

**Run MVP (Night 1):**

1. Clone repo → `cd hey-nova`
2. Create virtualenv: `python -m venv .venv && source .venv/bin/activate`
3. Install deps: `pip install faster-whisper openai sounddevice porcupine`
4. Run: `python core/main.py`
5. Speak: “Hey Nova” → test with “what’s my day?” or “open VS Code”

**Structure:**

```
hey-nova/
  core/
    main.py        # Entry point
    config.py      # API keys, voice, preferences
    wakeword/      # Porcupine wrapper
    stt/           # Whisper wrapper
    tts/           # macOS TTS wrapper
    brain/         # Router + persona prompt
    skills/        # Notion, apps, math, sysinfo
  server/          # (later) API for multi-device
  scripts/         # Setup & dev scripts
  README.md
```

---

## 💸 Cost (Current Implementation)

* **Free Components**: 
  * Wake word (Porcupine free tier), Whisper local processing, macOS TTS fallback
* **Current Cloud Costs**:
  * OpenAI LLM (GPT-4o-mini): ~$5–$15/mo for light personal use
  * Azure Neural TTS: ~$5–$9/mo for premium voice quality
* **Total**: Approximately $10–$25/month for full premium experience
* **Alternative**: Can run at **$0** using only local components (macOS TTS, local processing)

---

## 🚀 Roadmap

* **MVP (✅ Completed)**

  * ✅ Wake word, Whisper STT, OpenAI responses, Azure Neural TTS, intelligent skills
  * ✅ Custom "Hey Nova" wake word, continuous conversation, app control

* **Stage 2 (Next Phase)**

  * Proactive greetings, Notion integration, AppleScript automation
  * Background service, menubar app, launch agent

* **Stage 3 (Future)**

  * Multi-device support, memory store, cross-platform expansion
  * Windows, iPhone integration, centralized brain

* **Stage 4 (Long Term)**

  * Advanced neural TTS, security/encryption, enterprise features
  * Cross-device synchronization, proactive assistance

---

## 🚀 Current Features (MVP Complete)

**✅ What's Working Now:**

* **Custom Wake Word**: Trained "Hey Nova" model using Picovoice
* **Intelligent Math**: LLM-powered problem solving and explanations
* **App Control**: Launch applications, system automation
* **System Info**: Time, date, battery, volume status
* **Continuous Conversation**: Natural dialogue flow without repeating wake word
* **Premium Voice**: Azure Neural TTS with British female voice (Libby)
* **Professional Interface**: Clean terminal operation with error handling
* **Modular Architecture**: Easy to extend with new skills

**🎯 Key Improvements Made:**

* **LLM-First Design**: OpenAI GPT-4o-mini handles all intelligent responses
* **Audio Reliability**: Fixed PyAudio architecture issues for ARM64 Macs
* **Frame Processing**: Optimized audio streaming for wake word detection
* **Professional Code**: Clean, documented codebase with lowercase comments
* **Error Handling**: Robust fallbacks and graceful degradation

---

## 🌌 Vision

Hey Nova is not a toy chatbot. It’s a **personal AI butler** that:

* Greets you first with context, not scripts
* Speaks with a configurable voice/persona
* Controls your apps, reads your agenda, and automates workflows
* Lives across all your devices, but with a single “brain”
* Grows with you: from MacBook MVP → full cross-platform J.A.R.V.I.S.

---
## Mouhamed Mbengue 2025

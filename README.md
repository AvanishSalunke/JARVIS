# JARVIS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Phase 1 Active](https://img.shields.io/badge/Status-Phase%201%20Active-brightgreen)](https://github.com/[YOUR_USERNAME]/[YOUR_REPO])

> **Status:** This project is currently in active development.


An open-source, multi-phase project to build a modular, "Jarvis-like" AI assistant. This system is designed to be scalable and eventually integrate advanced reasoning, persistent memory, full speech interaction, vision, and OS-level automation.

##  Core Vision

The goal is to create a powerful, general-purpose assistant, not as a single monolithic application, but as a system of interconnected, intelligent modules. This modularity allows for focused development and easy scalability.

---

##  Project Roadmap

The project is broken down into several distinct phases. We are currently in **Phase 1**.

### ✅ Phase 1: The Core (Brain, Speech & Memory) (Current Focus)

**Goal:** Build a fully interactive, voice-enabled assistant with a persistent memory.

This foundational phase integrates the core intelligence with the primary user interface (voice) and memory systems.

* **Brain:** Using a **Mistral** LLM (via API) for reasoning, generation, and decision-making.
* **Speech-to-Text (STT):** An integrated module to transcribe user voice commands into text for the Brain.
* **Text-to-Speech (TTS):** A module to give the assistant a voice, converting the Brain's text responses back into audio.
* **Memory System:**
    * **Short-Term Memory:** A conversation buffer for contextual follow-ups.
    * **Long-Term Memory:** A **ChromaDB** vector database to store and recall facts, user preferences, and long-term information.
* **Orchestration:** Using **LangChain** to create a unified pipeline (STT -> Brain -> Memory -> TTS).

### ➡️ Phase 2: Vision (Image & Video)

**Goal:** Allow the assistant to see and understand the visual world.

* **Multimodal Models:** Integrate a model (e.g., LLaVA) to process and reason about images and videos.
* **Integration:** Connect the vision module to the Phase 1 Brain, allowing for questions like, "What do you see in this picture?"

### ➡️ Phase 3: OS Implementation & Automation

**Goal:** Enable the assistant to take action and perform tasks on the user's behalf.

* **Tooling:** Develop a "control" module with tools for OS-level automation (e.g., file management, opening applications, web browsing).
* **Agentic Behavior:** Evolve the Brain into a true agent that can use these tools to fulfill complex, multi-step requests (e.g., "Find the report from last week, summarize it, and email it to my boss").

---

## 🛠️ Technology Stack (Phase 1)

* **Language:** Python
* **Core LLM:** Mistral (via API)
* **Orchestration:** LangChain
* **Vector Database:** ChromaDB
* **API Server:** FastAPI (or Flask)
* **Speech-to-Text:** [e.g., Whisper, Google Speech-to-Text]
* **Text-to-Speech:** [e.g., gTTS, ElevenLabs, pyttsx3]

---

## 🏁 Getting Started

This project is in active development.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/[YOUR_REPO].git
    cd [YOUR_REPO]
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file and add your API keys and configuration (e.g., `MISTRAL_API_KEY`).

4.  **Run the application:**
    (Instructions to run your main `app.py` or `main.py`, e.g., using `uvicorn`)

---

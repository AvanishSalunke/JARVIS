# JARVIS - AI Personal Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Phase 1 Active](https://img.shields.io/badge/Status-Phase%201%20Active-brightgreen)](https://github.com/[YOUR_USERNAME]/[YOUR_REPO])


JARVIS is an AI-powered personal assistant designed to bridge the gap between intelligence and execution. Unlike conventional assistants that stop at conversation, JARVIS extends its capabilities into your local operating system—opening applications, managing system controls, navigating the web, and responding visually to the world around it.

At its core, JARVIS is a modular, locally-aware AI system that combines cloud-level reasoning with on-device control. It listens, understands, decides, and does things—bringing the concept of a truly functional AI assistant closer to reality.

##  Tech Stack

| **Category**              | **Technologies** |
|---------------------------|------------------|
| **Programming Languages** | [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://docs.python.org/3/) |
| **AI / LLM**              | [![Groq](https://img.shields.io/badge/Groq%20LLM-000000?style=for-the-badge)](https://groq.com/) |
| **Vision Models**         | [![BLIP](https://img.shields.io/badge/BLIP-6A5ACD?style=for-the-badge)](https://arxiv.org/abs/2201.12086) |
| **Memory / Vector DB**    | [![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge)](https://docs.trychroma.com/) |
| **Web Search**            | [![Serper](https://img.shields.io/badge/Serper-4285F4?style=for-the-badge)](https://serper.dev/) |
| **Backend Framework**     | [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) |
| **Local Automation**      | [![os](https://img.shields.io/badge/os-808080?style=for-the-badge)](https://docs.python.org/3/library/os.html) [![subprocess](https://img.shields.io/badge/subprocess-4B4B4B?style=for-the-badge)](https://docs.python.org/3/library/subprocess.html) [![PyAutoGUI](https://img.shields.io/badge/PyAutoGUI-3776AB?style=for-the-badge)](https://pyautogui.readthedocs.io/en/latest/) |
| **Tools**                 | [![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)](https://git-scm.com/doc) [![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://code.visualstudio.com/docs) |
| **Deployment / Runtime**  | [![Uvicorn](https://img.shields.io/badge/Uvicorn-121212?style=for-the-badge)](https://www.uvicorn.org/) |
                                                                                              
---

## 🏗 System Architecture

- ### 🧩 AI Brain Layer
   This layer is responsible for understanding and reasoning.
   
   **Powered by:** Groq LLM
   
   **Handles:**
   - Natural language understanding
   - Decision making
   - Task intent classification
   
   **Routes commands to:**
   - Conversational response
   - Vision module
   - Local agent



- ### 👁 Vision Module
   This module enables visual intelligence.
   
   **Uses:** BLIP for image captioning
   
   **Capabilities:**
   - Converts images into meaningful text descriptions
   
   **Can be extended to:**
   - Scene understanding
   - Visual question answering


- ### ⚙️ Local Agent
   This is where JARVIS becomes actionable.
   
   **Executes OS-level commands:**
   - Open / close applications
   - Adjust system volume
   - Control system processes
   - Launch websites
   
   **Runs locally for:**
   - Low latency
   - Security
   - Direct system access


---
## 🚀 How to Run JARVIS locally

JARVIS can be run locally for development and testing. A hosted version is planned and will be added soon.


#### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/JARVIS.git
cd JARVIS
```
#### 2️⃣ Move to backend directory
```bash
cd backend
```
#### 3️⃣ Create & Activate Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```
#### 4️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
#### 5️⃣ Set Environment Variables
Create a .env file in the root directory and add:

```bash
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
```

#### 6️⃣ Run the Backend Server
```python
python main.py
```
#### 7️⃣ Start frontend
Start a new terminal and move to frontend
```bash
cd frontend
```
Install dependencies and run
```bash
npm install
npm run dev
```


---

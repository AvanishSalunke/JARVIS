/* src/App.tsx */
import { useRef, useState, useEffect, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import * as api from "./api"; 
import Sidebar from "./components/Sidebar"; 
import "./App.css";

interface Message {
  sender: "user" | "jarvis";
  text: string;
}

function App() {
  // --- CORE STATE ---
  const [agentOnline, setAgentOnline] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  const imagePreviewUrl = useMemo(() => {
    if (selectedFile) return URL.createObjectURL(selectedFile);
    return null;
  }, [selectedFile]);

  useEffect(() => {
    return () => {
      if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    };
  }, [imagePreviewUrl]);
  
  // --- UI STATE ---
  const [showSidebar, setShowSidebar] = useState(false);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);

  // --- REFS ---
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  
  // --- AUDIO PLAYER REF (THE FIX) ---
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // 1. Scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // =====================
  // SIDEBAR ACTIONS
  // =====================

  const handleSelectChat = async (id: string) => {
    stopSpeaking(); // Stop talking when switching chats
    setActiveChatId(id);
    const history = await api.fetchChatHistory(id);
    
    const formatted: Message[] = history.map((h: { role: string; content: string }) => ({
        sender: h.role === "human" ? "user" : "jarvis",
        text: h.content
    }));
    
    setMessages(formatted);
  };

  const handleNewChat = async () => {
    stopSpeaking(); // Stop talking on new chat
    const newChat = await api.createNewChat();
    setActiveChatId(newChat.chat_id);
    setMessages([]); 
  };

  // Initial Load
  useEffect(() => {
    api.fetchChatList().then(chats => {
        if (chats.length > 0) {
            handleSelectChat(chats[0].chat_id);
        }
    });
  }, []);

  // Agent Status Check
  useEffect(() => {
    const checkAgent = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/agent-status");
        const data = await res.json();
        setAgentOnline(data.connected);
      } catch {
        setAgentOnline(false);
      }
    };

    checkAgent();
    const interval = setInterval(checkAgent, 3000); 
    return () => clearInterval(interval);
  }, []);

  // =====================
  // VOICE ENGINE
  // =====================

  const startRecording = async () => {
    stopSpeaking(); // Stop Jarvis if he's talking so he doesn't listen to himself
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await handleAudioSubmit(audioBlob);
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Microphone access denied or not available.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  // =====================
  // MESSAGE PROCESSING
  // =====================

  const handleAudioSubmit = async (audioBlob: Blob) => {
    setIsProcessing(true);
    try {
      const text = await api.sendAudio(audioBlob);
      if (text) {
        addMessage("user", text);
        await processResponse(text);
      }
    } catch (error) {
      console.error("Error sending audio:", error);
    }
    setIsProcessing(false);
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    // KEY FIX: Stop any current audio immediately when user sends a new message
    stopSpeaking();

    addMessage("user", textInput);
    const messageText = textInput;
    setTextInput("");
    setIsProcessing(true);
    await processResponse(messageText);
    setIsProcessing(false);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleImageAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Please choose an image first.");
      return;
    }
    if (!textInput.trim()) {
      alert("Please type a question about the image in the input box.");
      return;
    }

    stopSpeaking(); // Stop audio
    setIsProcessing(true);
    try {
      addMessage("user", `[Image: ${selectedFile.name}] ${textInput}`);
      const data = await api.sendImageQuestion(selectedFile, textInput, activeChatId);
      if (data.chat_id && data.chat_id !== activeChatId) setActiveChatId(data.chat_id);
      addMessage("jarvis", data.response);
      await playAudioResponse(data.response);
      setTextInput("");
      setSelectedFile(null);
      const el = document.getElementById("image-input") as HTMLInputElement | null;
      if (el) el.value = "";
    } catch (e) {
      console.error("Image ask error", e);
      addMessage("jarvis", "I couldn't process your image question right now.");
    }
    setIsProcessing(false);
  };

  const processResponse = async (text: string) => {
    try {
      const data = await api.sendMessage(text, activeChatId);
      
      if (data.chat_id && data.chat_id !== activeChatId) {
          setActiveChatId(data.chat_id);
      }

      addMessage("jarvis", data.response);
      await playAudioResponse(data.response);

    } catch (error) {
      console.error("Error fetching chat response:", error);
      addMessage("jarvis", "I'm having trouble connecting to my brain right now.");
    }
  };

  // =====================
  // TTS & ANIMATION (FIXED)
  // =====================

  // Helper to kill current audio
  const stopSpeaking = () => {
    if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current.currentTime = 0;
        audioPlayerRef.current = null;
    }
    setIsSpeaking(false);
  };

  const playAudioResponse = async (text: string) => {
    if (!text) return;

    // 1. Kill any existing audio before starting new one
    stopSpeaking();

    setIsSpeaking(true); 

    try {
        const res = await fetch("http://127.0.0.1:8000/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        // 2. Save reference to global ref so we can stop it later
        audioPlayerRef.current = audio;

        audio.onended = () => {
            setIsSpeaking(false);
            audioPlayerRef.current = null;
        };
        
        await audio.play();
    } catch (e) {
        console.error("TTS Error", e);
        setIsSpeaking(false);
    }
  };

  const addMessage = (sender: "user" | "jarvis", text: string) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  return (
    <div className="jarvis-container">
      {/* LEFT PANEL: Logo + Orb */}
      <div className="jarvis-left">
        <h1 className="jarvis-title">J.A.R.V.I.S</h1>
        <div className="orb-container">
          <div className={`arc-reactor 
            ${isRecording ? "listening" : ""} 
            ${isProcessing ? "processing" : ""} 
            ${isSpeaking ? "speaking" : ""}`}>
            <span className={`status-dot ${agentOnline ? "online" : "offline"}`} />
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: Chat + Input */}
      <div className="jarvis-right">
        <Sidebar 
          isOpen={showSidebar}
          activeChatId={activeChatId}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          onClose={() => setShowSidebar(false)}
        />

        <div className="chat-container">
          <div className="chat-window">
            {messages.length === 0 && <div className="system-text">System Online. Awaiting Input...</div>}
            {messages.map((msg, i) => {
              const lower = (msg.text || '').toLowerCase();
              const isError = lower.includes('attempted to process') || lower.includes("language model is unavailable");
              return (
                <div key={i} className={`message ${msg.sender} ${isError ? 'error' : ''}`}>
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              );
            })}
            <div ref={chatEndRef} />
          </div>

          <form className="input-area" onSubmit={selectedFile ? handleImageAsk : handleTextSubmit}>
            <input 
                type="text" 
                value={textInput} 
                onChange={(e) => setTextInput(e.target.value)} 
                placeholder={selectedFile ? "Ask about the image..." : "Type a command..."} 
                disabled={isProcessing || isRecording} 
            />
            
            <label htmlFor="image-input" className="btn">
                {selectedFile ? selectedFile.name.substring(0, 10) + "..." : "IMAGE"}
            </label>
            <input id="image-input" type="file" accept="image/*" onChange={handleImageChange} style={{ display: 'none' }} />
            
            <button type="button" className="btn" onClick={isRecording ? stopRecording : startRecording} disabled={isProcessing}>
                {isRecording ? "STOP" : "VOICE"}
            </button>
            
            {/* NEW MUTE BUTTON: Only shows when speaking */}
            {isSpeaking && (
                <button type="button" className="btn stop-btn" onClick={stopSpeaking} style={{backgroundColor: '#ff4444', color: 'white'}}>
                    MUTE
                </button>
            )}

            <button type="button" className="btn" onClick={() => setShowSidebar(!showSidebar)}>
                {showSidebar ? "HIDE" : "SHOW"}
            </button>
            
            <button type="submit" className="btn" disabled={(!textInput.trim() && !selectedFile) || isProcessing}>
                {selectedFile ? "ASK" : "SEND"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
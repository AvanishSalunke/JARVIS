/* src/App.tsx */
import { useRef, useState, useEffect } from "react";
import "./App.css";

// Type for chat messages
interface Message {
  sender: "user" | "jarvis";
  text: string;
}

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Refs for media
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- VOICE RECORDING FUNCTIONS ---
  const startRecording = async () => {
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
        
        // Stop all tracks to release mic
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      addMessage("jarvis", "Microphone access denied. Please check settings.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // --- SUBMISSION HANDLERS ---
  
  // 1. Handle Voice Input
  const handleAudioSubmit = async (audioBlob: Blob) => {
    setIsProcessing(true);
    const formData = new FormData();
    formData.append("file", audioBlob, "speech.webm");

    try {
      // 1. Send Audio to STT
      const res = await fetch("http://127.0.0.1:8000/stt", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      
      if (data.text) {
        addMessage("user", data.text);
        // 2. Process the text (Send to Brain/TTS)
        await processResponse(data.text);
      } else {
        addMessage("jarvis", "I didn't catch that.");
      }
    } catch (err) {
      console.error(err);
      addMessage("jarvis", "System Offline: Backend not reachable.");
    } finally {
      setIsProcessing(false);
    }
  };

  // 2. Handle Text Input
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    const userText = textInput;
    setTextInput(""); // Clear input
    addMessage("user", userText);
    
    setIsProcessing(true);
    await processResponse(userText);
    setIsProcessing(false);
  };

  // --- CORE LOGIC (BRAIN + TTS) ---
  const processResponse = async (text: string) => {
    // TODO: Connect your "Brain" / LLM here later. 
    // For now, we just Echo the text back via TTS.
    
    // Example: const brainResponse = await fetchBrain(text);
    const jarvisResponse = "You said: " + text; // Placeholder response
    
    addMessage("jarvis", jarvisResponse);
    await speakText(jarvisResponse);
  };

  const speakText = async (text: string) => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8001/tts?text=${encodeURIComponent(text)}`, // Note: Port 8001 for TTS
        { method: "POST" }
      );
      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = audioUrl;
        audioPlayerRef.current.play();
        setIsSpeaking(true);
        
        audioPlayerRef.current.onended = () => {
          setIsSpeaking(false);
        };
      }
    } catch (err) {
      console.error("TTS Error:", err);
    }
  };

  // Helper to add messages
  const addMessage = (sender: "user" | "jarvis", text: string) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  return (
    <div className="jarvis-container">
      {/* 1. STATUS HEADER */}
      <h1 style={{ letterSpacing: "5px", textShadow: "0 0 10px red" }}>
        J.A.R.V.I.S
      </h1>

      {/* 2. THE ARC REACTOR ORB */}
      <div className="orb-container">
        <div className={`arc-reactor 
          ${isRecording ? "listening" : ""} 
          ${isSpeaking ? "speaking" : ""} 
          ${isProcessing ? "processing" : ""}`}
        ></div>
      </div>

      {/* 3. CHAT HISTORY */}
      <div className="chat-window">
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#555", marginTop: "20%" }}>
            System Online. Awaiting Input...
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* 4. INPUT CONTROLS */}
      <form className="input-area" onSubmit={handleTextSubmit}>
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Type a command..."
          disabled={isProcessing || isRecording}
        />
        
        <button type="submit" disabled={!textInput || isProcessing}>
          SEND
        </button>

        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          className={isRecording ? "mic-active" : ""}
          disabled={isProcessing}
        >
          {isRecording ? "STOP" : "VOICE"}
        </button>
      </form>

      {/* Hidden Audio Player for TTS */}
      <audio ref={audioPlayerRef} hidden />
    </div>
  );
}

export default App;
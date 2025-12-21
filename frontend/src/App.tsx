import { useState, useRef } from "react";
import axios from "axios";
import { Mic, Square, Loader2 } from "lucide-react"; // Icons
import "./App.css";

// Basic type for chat messages
type Message = {
  role: "user" | "ai";
  text: string;
};

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  // Refs for recording and audio playback
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // 1. Start Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = handleStopRecording;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Microphone access denied!");
    }
  };

  // 2. Stop Recording & Send to Backend
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true); // Start "Thinking" animation
    }
  };

  const handleStopRecording = async () => {
    // Convert chunks to a single blob (file)
    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
    
    // Create a Form to send the file
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    try {
      // --- SEND TO PYTHON BACKEND ---
      // Make sure your Python server is running on port 8000!
      const response = await axios.post("http://127.0.0.1:8000/process-voice", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = response.data;

      // Update Chat Log
      setMessages((prev) => [
        ...prev,
        { role: "user", text: data.user_text },
        { role: "ai", text: data.jarvis_text },
      ]);

      // Play the Audio Response
      playResponse(data.audio_url);

    } catch (error) {
      console.error("Error sending audio:", error);
      setMessages((prev) => [...prev, { role: "ai", text: "Error: I couldn't hear you." }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // 3. Play Audio Response
  const playResponse = (url: string) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = url;
      audioPlayerRef.current.play();
      setIsSpeaking(true);
      
      audioPlayerRef.current.onended = () => setIsSpeaking(false);
    }
  };

  // --- UI RENDER ---
  return (
    <div className="container">
      <h1>J.A.R.V.I.S</h1>

      {/* The Visualizer Orb */}
      <div className="orb-container">
        <div 
          className={`orb ${isRecording ? "listening" : ""} ${isProcessing ? "thinking" : ""} ${isSpeaking ? "speaking" : ""}`} 
        />
      </div>

      {/* Status Text */}
      <p style={{ minHeight: "24px" }}>
        {isRecording ? "Listening..." : isProcessing ? "Thinking..." : isSpeaking ? "Speaking..." : "Online"}
      </p>

      {/* Mic Button */}
      <button 
        className={`mic-button ${isRecording ? "active" : ""}`}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing || isSpeaking}
      >
        {isProcessing ? <Loader2 className="animate-spin" /> : isRecording ? <Square fill="currentColor" /> : <Mic />}
      </button>

      {/* Chat Log */}
      <div className="chat-log">
        {messages.length === 0 && <p style={{color:"#555"}}>System logs empty. Start conversation.</p>}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <strong>{msg.role === "user" ? "YOU: " : "JARVIS: "}</strong> 
            {msg.text}
          </div>
        ))}
      </div>

      {/* Invisible Audio Player */}
      <audio ref={audioPlayerRef} hidden />
    </div>
  );
}

export default App;
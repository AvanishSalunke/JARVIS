/* src/App.tsx */
import { useRef, useState, useEffect } from "react";
import ReactMarkdown from "react-markdown"; // <--- Added Import
import "./App.css";

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

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const audioQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef(false);

  // Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // =====================
  // VOICE RECORDING
  // =====================

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
  // AUDIO SUBMIT
  // =====================

  const handleAudioSubmit = async (audioBlob: Blob) => {
    setIsProcessing(true);

    const formData = new FormData();
    formData.append("file", audioBlob, "speech.webm");

    try {
      const res = await fetch("http://127.0.0.1:8000/stt", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.text) {
        addMessage("user", data.text);
        await processResponse(data.text);
      }
    } catch (error) {
      console.error("Error sending audio:", error);
    }

    setIsProcessing(false);
  };

  // =====================
  // TEXT SUBMIT
  // =====================

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    addMessage("user", textInput);
    setIsProcessing(true);
    await processResponse(textInput);
    setTextInput("");
    setIsProcessing(false);
  };

  // =====================
  // LLM LOGIC
  // =====================

  const processResponse = async (text: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();
      addMessage("jarvis", data.response);
      await speakText(data.response);
    } catch (error) {
      console.error("Error fetching chat response:", error);
      addMessage("jarvis", "I'm having trouble connecting to my brain right now.");
    }
  };

  // =====================
  // UPDATED TTS (Sentence Queueing)
  // =====================

  const playNextInQueue = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsSpeaking(false);
      return;
    }

    isPlayingRef.current = true;
    setIsSpeaking(true);

    const nextAudioUrl = audioQueueRef.current.shift(); // Take first item

    if (audioPlayerRef.current && nextAudioUrl) {
      audioPlayerRef.current.src = nextAudioUrl;
      audioPlayerRef.current.play();

      // When this sentence finishes, play the next one automatically
      audioPlayerRef.current.onended = playNextInQueue;
    }
  };

  const speakText = async (text: string) => {
    if (!text) return;

    // 1. Split text into sentences (by . ! ?)
    // This regex looks for punctuation and keeps it attached to the sentence
    const sentences = text.match(/[^\.!\?]+[\.!\?]+/g) || [text];

    for (const sentence of sentences) {
      try {
        // 2. Fetch audio for THIS sentence only
        const res = await fetch(
          `http://127.0.0.1:8000/tts?text=${encodeURIComponent(sentence)}`,
          { method: "POST" }
        );

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        // 3. Add to queue
        audioQueueRef.current.push(url);

        // 4. If nothing is playing, start the queue immediately
        if (!isPlayingRef.current) {
          playNextInQueue();
        }
      } catch (error) {
        console.error("Error generating speech segment:", error);
      }
    }
  };
  const addMessage = (sender: "user" | "jarvis", text: string) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  return (
    <div className="jarvis-container">
      {/* HEADER */}
      <h1 style={{ letterSpacing: "5px", textShadow: "0 0 10px red" }}>
        J.A.R.V.I.S
      </h1>

      {/* ORB */}
      <div className="orb-container">
        <div
          className={`arc-reactor 
            ${isRecording ? "listening" : ""} 
            ${isProcessing ? "processing" : ""} 
            ${isSpeaking ? "speaking" : ""}`}
        />
      </div>

      {/* CHAT */}
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="system-text">System Online. Awaiting Input...</div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            {/* 👇 UPDATED: Now rendering Markdown */}
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        ))}

        <div ref={chatEndRef} />
      </div>

      {/* INPUT */}
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

        {/* Placeholder button from your original code */}
        <button type="button" disabled={isProcessing}>
          SHOW
        </button>
      </form>

      <audio ref={audioPlayerRef} hidden />
    </div>
  );
}

export default App;
/* src/components/Login.tsx */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import "../App.css";

export default function Login() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Endpoints
    const endpoint = isLogin ? "http://127.0.0.1:8000/token" : "http://127.0.0.1:8000/signup";
    
    let body;
    let headers = {};

    if (isLogin) {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
      body = formData;
      headers = { "Content-Type": "application/x-www-form-urlencoded" };
    } else {
      body = JSON.stringify({ username, password });
      headers = { "Content-Type": "application/json" };
    }

    try {
      const res = await fetch(endpoint, { method: "POST", headers, body });
      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || "Authentication failed");

      if (isLogin) {
        localStorage.setItem("jarvis_token", data.access_token);
        // Navigate to the main chat interface
        navigate("/chat"); 
      } else {
        setIsLogin(true);
        setError("Identity Verified. Proceed to Login.");
      }
    } catch (err: any) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="cinematic-overlay login-bg">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="login-panel"
      >
        {/* Decorative Corners */}
        <div className="hud-bracket hb-tl"></div>
        <div className="hud-bracket hb-tr"></div>
        <div className="hud-bracket hb-bl"></div>
        <div className="hud-bracket hb-br"></div>

        <h2 className="login-title">
            {isLogin ? "System Login" : "New User"}
        </h2>

        {error && <div className="message error" style={{textAlign: 'center'}}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <input 
            className="login-input"
            type="text" 
            placeholder="USERNAME"
            value={username} 
            onChange={e => setUsername(e.target.value)}
          />
          <input 
            className="login-input"
            type="password" 
            placeholder="PASSWORD"
            value={password} 
            onChange={e => setPassword(e.target.value)}
          />
          
          <button 
            type="submit" 
            className="btn btn--primary" 
            style={{ width: "100%", padding: "15px", fontSize: "1.1rem", marginTop: "10px" }}
          >
            {loading ? "PROCESSING..." : (isLogin ? "INITIALIZE" : "REGISTER")}
          </button>
        </form>

        <button 
            className="btn btn--ghost" 
            onClick={() => setIsLogin(!isLogin)}
            style={{ width: "100%", fontSize: "0.9rem", opacity: 0.7, border: 'none' }}
        >
          {isLogin ? "> Create New Protocol" : "> Return to Login"}
        </button>
      </motion.div>
    </div>
  );
}
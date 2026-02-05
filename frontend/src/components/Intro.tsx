/* src/components/Intro.tsx */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import "../App.css"; // Imports your CSS including the new stuff at the bottom

export default function Intro() {
  const navigate = useNavigate();

  useEffect(() => {
    // Wait 4 seconds, then go to login
    const timer = setTimeout(() => {
      navigate("/login");
    }, 4000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="cinematic-overlay">
      {/* The Big Arc Reactor Boot Animation */}
      <motion.div 
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        className="boot-reactor-container"
      >
        <div className="boot-ring br1" />
        <div className="boot-ring br2" />
        <div className="boot-ring br3" />
        <div className="boot-core" />
      </motion.div>

      {/* Loading Text */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5, duration: 1 }}
        style={{ 
          fontFamily: "'Rajdhani', sans-serif", 
          fontSize: "1.5rem", 
          letterSpacing: "5px", 
          color: "#00ffff",
          textShadow: "0 0 10px #00ffff"
        }}
      >
        INITIALIZING J.A.R.V.I.S...
      </motion.div>
      
      {/* Loading Bar */}
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: "300px" }}
        transition={{ delay: 2, duration: 1.5 }}
        style={{ height: "2px", background: "#00ffff", marginTop: "20px", boxShadow: "0 0 15px #00ffff" }}
      />
    </div>
  );
}
/* src/App.tsx */
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Intro from "./components/Intro";
import Login from "./components/Login";
import ChatInterface from "./components/ChatInterface"; // Your existing main chat component
import "./App.css";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem("jarvis_token");
  return token ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Intro />} />
        <Route path="/login" element={<Login />} />
        <Route 
          path="/chat" 
          element={
            <ProtectedRoute>
              <ChatInterface />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;
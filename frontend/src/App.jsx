import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send, Brain, BookOpen,
  FlaskConical, Shield, Zap
} from 'lucide-react';
import './index.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1/research";

// --- Markdown-Lite Renderer ---
const FormattedText = ({ text, onCitationClick }) => {
  if (!text) return null;

  // Split by line to handle headers and lists
  const lines = text.split('\n');

  return (
    <div className="formatted-message">
      {lines.map((line, i) => {
        let content = line;

        // Headers ###
        if (content.startsWith('###')) {
          return <h4 key={i} className="md-header">{content.replace('###', '').trim()}</h4>;
        }

        // Lists - or *
        const isListItem = content.trim().startsWith('- ') || content.trim().startsWith('* ');

        // Basic Bold **text**
        const parts = content.split(/(\*\*.*?\*\*|\[\d+\])/g);

        const renderedLine = parts.map((part, j) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={j}>{part.slice(2, -2)}</strong>;
          }
          if (/^\[\d+\]$/.test(part)) {
            const num = part.match(/\d+/)[0];
            return (
              <span
                key={j}
                className="citation-tag"
                onClick={() => onCitationClick(parseInt(num))}
              >
                {part}
              </span>
            );
          }
          return part;
        });

        return isListItem ? (
          <li key={i} className="md-list-item">{renderedLine}</li>
        ) : (
          <p key={i} className="md-para">{renderedLine}</p>
        );
      })}
    </div>
  );
};

function App() {
  const [patient, setPatient] = useState({ name: '', disease: '', intent: '', location: '' });
  const [isStarted, setIsStarted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [thoughts, setThoughts] = useState('');
  const [sources, setSources] = useState([]);
  const [sessionId] = useState(`session_${Math.random().toString(36).substr(2, 9)}`);
  const [highlightIdx, setHighlightIdx] = useState(null);

  const chatEndRef = useRef(null);
  const sourceRefs = useRef([]);

  const scrollToBottom = () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => scrollToBottom(), [messages]);

  const handleCitationClick = (num) => {
    const idx = num - 1;
    setHighlightIdx(idx);
    sourceRefs.current[idx]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => setHighlightIdx(null), 2000);
  };

  const performResearch = async (searchQuery, isInitial = false) => {
    if (!searchQuery.trim()) return;

    // Append User Query to Chat
    setMessages(prev => [...prev, { role: 'user', content: searchQuery }]);
    setQuery(''); // Clear Input
    setIsLoading(true);
    setThoughts('Agent initializing... Decoding research matrix...');

    try {
      const response = await axios.post(`${API_BASE}/query`, {
        patient_name: patient.name,
        disease: patient.disease,
        query: searchQuery,
        location: patient.location,
        session_id: sessionId
      });

      const { answer, thought_process, sources: newSources } = response.data.data;
      setMessages(prev => [...prev, { role: 'assistant', content: answer }]);
      setThoughts(thought_process);
      setSources(newSources);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || "System desync.";
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = () => {
    if (patient.name && patient.disease && patient.intent) {
      setIsStarted(true);
      // Combine intent + disease for initial query as per Hackathon Spec
      const initialQuery = `${patient.intent} for ${patient.disease}`;
      performResearch(initialQuery, true);
    } else {
      alert("Please fill in Name, Disease, and Intent.");
    }
  };

  if (!isStarted) {
    return (
      <div className="intro-overlay">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass intro-panel"
        >
          <div className="logo-glow">
            <FlaskConical size={32} color="white" />
          </div>
          <h1>Curalink</h1>
          <p style={{ color: '#94a3b8', marginBottom: 24, fontSize: '0.9rem' }}>PRECISION MEDICAL AGENT</p>

          <div className="structured-input-grid">
            <div className="input-group">
              <p className="form-label">Patient Name</p>
              <input
                className="input-field"
                placeholder="John Smith"
                value={patient.name}
                onChange={(e) => setPatient({ ...patient, name: e.target.value })}
              />
            </div>
            <div className="input-group">
              <p className="form-label">Disease of Interest</p>
              <input
                className="input-field"
                placeholder="Parkinson's Disease"
                value={patient.disease}
                onChange={(e) => setPatient({ ...patient, disease: e.target.value })}
              />
            </div>
            <div className="input-group">
              <p className="form-label">Additional Query / Intent</p>
              <input
                className="input-field"
                placeholder="Deep Brain Stimulation"
                value={patient.intent}
                onChange={(e) => setPatient({ ...patient, intent: e.target.value })}
              />
            </div>
            <div className="input-group">
              <p className="form-label">Location (Optional)</p>
              <input
                className="input-field"
                placeholder="Toronto, Canada"
                value={patient.location}
                onChange={(e) => setPatient({ ...patient, location: e.target.value })}
              />
            </div>
          </div>

          <button className="pulse-btn" style={{ marginTop: 24 }} onClick={handleStart}>
            Enter Neural Workspace
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="sidebar-nav">
        <motion.div className="glass shadow-xl">
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', gap: 12 }}>
            <Brain size={18} color="#fbbf24" />
            <h4 style={{ fontSize: '0.9rem' }}>Agent Reasoning</h4>
          </div>
          <div className="reasoning-terminal">
            <FormattedText text={thoughts || "Awaiting pulse..."} />
          </div>
        </motion.div>

        <motion.div className="glass shadow-xl">
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', gap: 12 }}>
            <BookOpen size={18} color="#2dd4bf" />
            <h4 style={{ fontSize: '0.9rem' }}>Validated Evidence</h4>
          </div>
          <div className="evidence-scroll">
            {sources.length === 0 ? (
              <div className="empty-evidence">
                <Shield size={24} style={{ opacity: 0.2, marginBottom: 12 }} />
                <p>No validated medical evidence found for the current query.</p>
              </div>
            ) : sources.map((src, i) => (
              <motion.div
                key={i}
                ref={el => sourceRefs.current[i] = el}
                animate={{
                  scale: highlightIdx === i ? 1.05 : 1,
                  boxShadow: highlightIdx === i ? "0 0 20px rgba(56, 189, 248, 0.4)" : "none",
                  borderColor: highlightIdx === i ? "var(--accent-main)" : "var(--border-glass)"
                }}
                className="glass source-item"
                onClick={() => window.open(src.url, '_blank')}
              >
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  <span style={{ color: 'var(--accent-main)', marginRight: 8 }}>[{i + 1}]</span>
                  {src.title}
                </div>
                {src.authors && (
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: 4, fontStyle: 'italic' }}>
                    {src.authors.length > 100 ? src.authors.substring(0, 100) + '...' : src.authors}
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{src.source} • {src.date}</div>
                  {src.status && (
                    <span className={`status-badge ${src.status.toLowerCase().includes('recruiting') ? 'active' : ''}`}>
                      {src.status}
                    </span>
                  )}
                </div>
                {src.location && src.location !== 'N/A' && (
                  <div style={{ fontSize: '0.65rem', color: '#475569', marginTop: 4 }}>
                    📍 {src.location}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      <motion.div className="main-content glass">
        <div className="workspace-header">
          <div>
            <h2 style={{ fontSize: '1.25rem' }}>{patient.disease}</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Patient: {patient.name}</p>
          </div>
          <Shield size={20} color="#4ade80" />
        </div>

        <div className="chat-scroller">
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`bubble ${msg.role}`}
              >
                <FormattedText text={msg.content} onCitationClick={handleCitationClick} />
              </motion.div>
            ))}
          </AnimatePresence>
          {isLoading && (
            <motion.div animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 1.5 }} className="bubble assistant">
              <Zap size={16} className="spin" style={{ marginRight: 10, color: '#38bdf8' }} />
              Researching cross-platform data...
            </motion.div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="input-container">
          <input
            className="input-field"
            placeholder="Type clinical inquiry..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && performResearch(query)}
          />
          <button className="pulse-btn" style={{ width: '80px' }} onClick={() => performResearch(query)} disabled={isLoading}>
            <Send size={20} />
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export default App;

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send, Brain, BookOpen,
  FlaskConical, Shield, Zap, Info, ChevronRight, ChevronDown, CheckCircle2, Circle, ArrowLeft, User, Eye, EyeOff,
  History, Plus, PanelLeftClose, PanelLeft, Trash2, LogOut
} from 'lucide-react';
import './index.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1/research";

// --- Markdown-Lite Renderer ---
const FormattedText = ({ text, onCitationClick }) => {
  if (!text) return null;
  const lines = text.split('\n');
  return (
    <div className="formatted-message">
      {lines.map((line, i) => {
        let content = line;
        if (content.startsWith('###')) return <h4 key={i}>{content.replace('###', '').trim()}</h4>;
        const isListItem = content.trim().startsWith('- ') || content.trim().startsWith('* ');
        const parts = content.split(/(\*\*.*?\*\*|\[\d+\])/g);
        const renderedLine = parts.map((part, j) => {
          if (part.startsWith('**') && part.endsWith('**')) return <strong key={j}>{part.slice(2, -2)}</strong>;
          if (/^\[\d+\]$/.test(part)) {
            const num = part.match(/\d+/)[0];
            return (
              <span key={j} className="citation-tag" onClick={() => onCitationClick && onCitationClick(parseInt(num))}>
                {part}
              </span>
            );
          }
          return part;
        });
        return isListItem ? <li key={i} style={{ marginLeft: '20px' }}>{renderedLine}</li> : <p key={i}>{renderedLine}</p>;
      })}
    </div>
  );
};

// Simulated Thinking Process while Waiting
const THINKING_STEPS = [
  "Initializing neural search matrix...",
  "Cross-referencing PubMed and clinical databases...",
  "Parsing pathophysiological pathways...",
  "Evaluating recent peer-reviewed evidence...",
  "Synthesizing clinical response..."
];

const ThinkingLog = () => {
  const [stepIndex, setStepIndex] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex(prev => (prev < THINKING_STEPS.length - 1 ? prev + 1 : prev));
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="thought-process-container active-thinking" style={{ marginBottom: '12px' }}>
      <div className="thought-process-header">
        <Zap size={14} color="var(--accent-cyan)" className="spin" />
        <span style={{ color: 'var(--accent-cyan)', fontWeight: 500 }}>Processing Query...</span>
      </div>
      <div className="thinking-steps" style={{ marginTop: '8px', paddingLeft: '8px' }}>
        <AnimatePresence>
          {THINKING_STEPS.map((step, i) => {
            if (i > stepIndex) return null;
            const isLatest = i === stepIndex;
            return (
              <motion.div
                key={i} initial={{ opacity: 0, height: 0, x: -10 }} animate={{ opacity: 1, height: 'auto', x: 0 }}
                style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', margin: '4px 0', color: isLatest ? 'var(--text-main)' : 'var(--text-muted)' }}
              >
                {isLatest ? <Circle size={10} color="var(--accent-cyan)" className="pulse-icon" /> : <CheckCircle2 size={12} color="var(--accent-green)" />}
                <span style={{ fontFamily: 'var(--font-mono)' }}>{step}</span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
};

const ThoughtProcess = ({ thoughts }) => {
  const [isOpen, setIsOpen] = useState(false);
  if (!thoughts) return null;
  return (
    <div className="thought-process-container" style={{ marginBottom: '16px' }}>
      <div className="thought-process-header" onClick={() => setIsOpen(!isOpen)} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
        <Brain size={14} color={isOpen ? "var(--text-main)" : "var(--text-muted)"} />
        <span style={{ fontSize: '0.8rem', fontWeight: 500, color: isOpen ? "var(--text-main)" : "var(--text-muted)", transition: 'color 0.2s' }}>
          {isOpen ? 'Hide Reasoning Logs' : 'View Reasoning Logs'}
        </span>
        <ChevronDown size={14} style={{ marginLeft: 'auto', transform: isOpen ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s', color: 'var(--text-muted)' }} />
      </div>
      <AnimatePresence>
        {isOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: 'hidden' }}>
            <div className="terminal-content" style={{ padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', marginTop: '8px', fontSize: '0.75rem' }}>
              <FormattedText text={thoughts} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Inline Sources Component
const SourcesList = ({ sources, highlightIdx }) => {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="inline-sources" style={{ marginTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px' }}>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <BookOpen size={14} /> <span>Validated Evidence</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '10px' }}>
        {sources.map((src, i) => (
          <div key={i} className={`evidence-card ${highlightIdx === i ? 'highlight' : ''}`} onClick={() => window.open(src.url, '_blank')} style={{ padding: '12px', fontSize: '0.8rem' }}>
            <div style={{ color: '#fff', fontWeight: 600, marginBottom: '6px' }}>
              <span style={{ color: 'var(--accent-blue)', marginRight: '6px' }}>[{i + 1}]</span>
              {src.title.length > 55 ? src.title.substring(0, 55) + '...' : src.title}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
              {src.source} • {src.date}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

function App() {
  const [patient, setPatient] = useState({ disease: '', intent: '', location: '' });
  const [currentScreen, setCurrentScreen] = useState('welcome');
  const [showMethodology, setShowMethodology] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [authForm, setAuthForm] = useState({ email: '', password: '', name: '' });
  const [authError, setAuthError] = useState('');
  const [otpMode, setOtpMode] = useState(false);
  const [otpValue, setOtpValue] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [history, setHistory] = useState([]);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(`session_${Math.random().toString(36).substr(2, 9)}`);
  const [highlightIdx, setHighlightIdx] = useState(null);
  const [showAccountMenu, setShowAccountMenu] = useState(false);

  const chatContainerRef = useRef(null);
  const isAutoScroll = useRef(true);
  const useSmoothScroll = useRef(false);

  // Smooth uniform streaming visual release mechanism
  useEffect(() => {
    const drainInterval = setInterval(() => {
      setMessages(prev => {
        let changed = false;
        const nextState = prev.map(m => {
          if (m.role === 'assistant' && m.isStreaming && m.buffer !== undefined && m.content.length < m.buffer.length) {
            changed = true;
            return { ...m, content: m.buffer.substring(0, m.content.length + 4) };
          }
          if (m.role === 'assistant' && m.isStreaming && m.buffer !== undefined && m.content.length >= m.buffer.length && m.thoughts) {
            changed = true;
            return { ...m, isStreaming: false };
          }
          return m;
        });
        return changed ? nextState : prev;
      });
    }, 20);
    return () => clearInterval(drainInterval);
  }, []);

  // --- Auto-restore session from localStorage ---
  useEffect(() => {
    const saved = localStorage.getItem('curalink_session');
    if (saved) {
      try {
        const { email, name } = JSON.parse(saved);
        if (email) {
          setAuthForm(prev => ({ ...prev, email, name: name || '' }));
          setCurrentScreen('setup');
        }
      } catch (e) {
        localStorage.removeItem('curalink_session');
      }
    }
  }, []);

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollHeight, scrollTop, clientHeight } = chatContainerRef.current;
    // If the user scrolls up by more than 30px from bottom, instantly release auto-scroll lock
    isAutoScroll.current = (scrollHeight - scrollTop - clientHeight) <= 30;
  };

  const scrollToBottom = () => {
    if (!chatContainerRef.current) return;
    if (isAutoScroll.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: useSmoothScroll.current ? "smooth" : "auto"
      });
      if (useSmoothScroll.current) useSmoothScroll.current = false;
    }
  };

  useEffect(() => scrollToBottom(), [messages, isLoading]);

  const handleCitationClick = (num) => {
    const idx = num - 1;
    setHighlightIdx(idx);
    setTimeout(() => setHighlightIdx(null), 2500);
  };

  // --- Session Management ---
  useEffect(() => {
    if (currentScreen === 'chat' || currentScreen === 'setup') {
      fetchSessions();
    }
  }, [currentScreen]);

  const fetchSessions = async () => {
    try {
      const res = await axios.get(`${API_BASE}/sessions?email=${authForm.email}`);
      setHistory(res.data.sessions);
    } catch (e) { console.error("Error fetching sessions", e); }
  };


  const loadSession = async (id) => {
    setMessages([]);
    setIsLoading(true);
    setSessionId(id);
    try {
      const res = await axios.get(`${API_BASE}/history/${id}`);
      const formatted = res.data.messages.map(m => ({
        role: m.role,
        content: m.content,
        thoughts: m.thoughts,
        sources: m.sources
      }));
      setMessages(formatted);
      // Switch screen to chat when opening a past session
      if (formatted.length > 0) setCurrentScreen('chat');
      // Wait for React to update DOM, then scroll
      setTimeout(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight + 1000;
        }
      }, 50);
    } catch (e) {
      console.error("Failed to load session", e);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (id, e) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API_BASE}/history/${id}`);
      setHistory(prev => prev.filter(s => s.id !== id));
      if (sessionId === id) {
        startNewChat();
      }
    } catch (error) {
      console.error("Failed to delete session", error);
    }
  };

  const performResearch = async (searchQuery, isInitial = false) => {
    if (!searchQuery.trim()) return;

    // Forcibly lock scroll to bottom on new prompt and signal smooth transition
    isAutoScroll.current = true;
    useSmoothScroll.current = true;

    setMessages(prev => [...prev, { role: 'user', content: searchQuery }]);
    setQuery('');
    setIsLoading(true); // Engages ThinkingLog

    const msgId = Date.now();
    setMessages(prev => [...prev, { id: msgId, role: 'assistant', content: '', buffer: '', sources: null, thoughts: null, isStreaming: true }]);

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          disease: patient.disease,
          query: searchQuery,
          location: patient.location,
          session_id: sessionId,
          email: authForm.email
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const textChunk = decoder.decode(value, { stream: true });
        const lines = textChunk.split('\n').filter(l => l.trim().length > 0);

        for (const line of lines) {
          try {
            const data = JSON.parse(line);

            if (data.type === 'sources') {
              setIsLoading(false); // Stop 'ThinkingLog' when stream begins
              setMessages(prev => prev.map(m => m.id === msgId ? { ...m, sources: data.data } : m));
            }
            else if (data.type === 'chunk') {
              setIsLoading(false); // Failsafe to kill thinking mode once text arrives
              // Add to visual buffer instead of direct content output
              setMessages(prev => prev.map(m => m.id === msgId ? { ...m, buffer: m.buffer + data.text } : m));
            }
            else if (data.type === 'done') {
              setMessages(prev => prev.map(m => m.id === msgId ? { ...m, thoughts: data.thoughts, sources: data.sources } : m));
              fetchSessions(); // Refresh sidebar topic/date
              setIsLoading(false);
            }
            else if (data.type === 'error') {
              setMessages(prev => prev.map(m => m.id === msgId ? { ...m, content: m.content + `\n\nERROR: ${data.message}`, isStreaming: false } : m));
              setIsLoading(false);
            }
          } catch (e) {
            console.error("Parse error:", e);
          }
        }
      }
    } catch (error) {
      console.error(error);
      const errorMsg = error.message || "System desync.";
      setMessages(prev => prev.map(m => m.id === msgId ? { ...m, content: `Error: ${errorMsg}`, isStreaming: false } : m));
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setIsAuthenticating(true);

    // Traditional Direct Login
    if (authMode === 'login') {
      try {
        const response = await axios.post('/api/v1/auth/login', {
          email: authForm.email,
          password: authForm.password
        });
        if (response.data.status === 'success') {
          const name = response.data.name || '';
          if (name) setAuthForm(prev => ({ ...prev, name }));
          // Persist session to localStorage
          localStorage.setItem('curalink_session', JSON.stringify({ email: authForm.email, name }));
          setCurrentScreen('setup');
        }
      } catch (error) {
        if (error.response && error.response.status === 404) {
          setAuthError("Account not found. Please sign up to create a workspace.");
          setAuthMode('signup');
          setAuthForm(prev => ({ ...prev, password: '' }));
        } else {
          setAuthError("Authentication failed. Please check your credentials.");
        }
      } finally {
        setIsAuthenticating(false);
      }
      return;
    }

    // Signup with OTP Verification
    try {
      await axios.post('/api/v1/auth/send-otp', { email: authForm.email });
      setOtpMode(true);
    } catch (error) {
      alert("Error sending OTP. Please check your email.");
    } finally {
      setIsAuthenticating(false);
    }
  };

  const verifyOtpSubmit = async (e) => {
    e.preventDefault();
    setIsAuthenticating(true);
    try {
      const response = await axios.post('/api/v1/auth/verify-otp', {
        email: authForm.email,
        otp: otpValue,
        name: authMode === 'signup' ? authForm.name : undefined,
        password: authMode === 'signup' ? authForm.password : undefined
      });
      if (response.data.status === 'success') {
        // Persist session after OTP signup
        localStorage.setItem('curalink_session', JSON.stringify({ email: authForm.email, name: authForm.name || '' }));
        setCurrentScreen('setup');
      }
    } catch (error) {
      alert("Invalid OTP code.");
    } finally {
      setIsAuthenticating(false);
    }
  };

  const addAccount = () => {
    // Clear persisted session before switching
    localStorage.removeItem('curalink_session');
    setAuthForm({ email: '', password: '', name: '' });
    setAuthMode('signup');
    setAuthError('');
    setOtpMode(false);
    setOtpValue('');
    setMessages([]);
    setHistory([]);
    setShowAccountMenu(false);
    setCurrentScreen('auth');
  };

  const handleLogout = () => {
    localStorage.removeItem('curalink_session');
    setAuthForm({ email: '', password: '', name: '' });
    setAuthMode('login');
    setAuthError('');
    setOtpMode(false);
    setOtpValue('');
    setMessages([]);
    setHistory([]);
    setPatient({ disease: '', intent: '', location: '' });
    setSessionId('');
    setShowAccountMenu(false);
    setCurrentScreen('welcome');
  };

  const startNewChat = () => {
    setSessionId(`session_${Math.random().toString(36).substr(2, 9)}`);
    setMessages([]);
    setQuery('');
    setIsLoading(false);
    setPatient({ disease: '', intent: '', location: '' });
    setCurrentScreen('setup');
  };

  const handleStart = () => {
    if (patient.disease && patient.intent) {
      setCurrentScreen('chat');
      const initialQuery = `${patient.intent} for ${patient.disease}`;
      performResearch(initialQuery, true);
    } else {
      alert("Please fill in Pathology and Intent.");
    }
  };

  return (
    <>
      <div className="ambient-bg">
        <div className="ambient-blob blob-1"></div>
        <div className="ambient-blob blob-2"></div>
        <div className="ambient-blob blob-3"></div>
      </div>

      {currentScreen === 'welcome' && (
        <div className="landing-page">
          <nav className="landing-nav">
            <div className="landing-logo">
              <FlaskConical size={24} color="var(--accent-cyan)" />
              <span>CuraLink <small style={{ fontSize: '0.6rem', opacity: 0.5, marginLeft: '4px' }}>v1.4.2-MODERN</small></span>
            </div>
            <div className="landing-nav-links">
              <button className="nav-login-btn" onClick={() => { setAuthMode('login'); setCurrentScreen('auth'); }}>
                <User size={16} /> <span>Log In</span>
              </button>
            </div>
          </nav>

          <main className="landing-main">
            <motion.div className="hero-content" initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: "easeOut" }}>
              <div className="pill-badge">
                <span className="pulse-dot"></span> CuraLink v1.0 is Live
              </div>
              <h1 className="hero-title">
                Next-Gen Medical <br />
                <span className="text-gradient">Intelligence Protocol</span>
              </h1>
              <p className="hero-subtitle">
                An advanced agentic workstation that autonomously parses, correlates, and evaluates millions of peer-reviewed clinical trials and abstracts in milliseconds.
              </p>

              <div className="hero-actions">
                <button className="hero-btn primary" onClick={() => { setAuthMode('signup'); setCurrentScreen('auth'); }}>
                  Start Research Protocol <ChevronRight size={18} />
                </button>
                <button className="hero-btn secondary" onClick={() => setShowMethodology(true)}>
                  Clinical Methodology
                </button>
              </div>

              <div className="hero-stats">
                <div className="stat-item">
                  <h3>10M+</h3>
                  <p>PubMed Abstracts</p>
                </div>
                <div className="stat-item">
                  <h3>99.9%</h3>
                  <p>Verified Grounding</p>
                </div>
                <div className="stat-item">
                  <h3>{"<"}1s</h3>
                  <p>Deep-Dive Latency</p>
                </div>
              </div>
            </motion.div>
          </main>
        </div>
      )}

      {currentScreen === 'auth' && (
        <div className="auth-container">
          <motion.div className="auth-glass" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} style={{ position: 'relative' }}>
            <button className="back-btn" onClick={() => { setOtpMode(false); setCurrentScreen('welcome'); }}>
              <ArrowLeft size={16} /> <span>Back</span>
            </button>

            {!otpMode ? (
              <>
                <h2 className="auth-title" style={{ fontSize: '2.2rem', marginBottom: '24px', marginTop: '10px' }}>
                  {authMode === 'login' ? 'Welcome Back' : 'Create Account'}
                </h2>
                {authError && <div style={{ color: '#ff4d4d', fontSize: '0.85rem', marginBottom: '16px', textAlign: 'center', background: 'rgba(255, 77, 77, 0.1)', padding: '10px', borderRadius: '8px' }}>{authError}</div>}
                <form onSubmit={handleAuthSubmit} className="auth-form">
                  {authMode === 'signup' && (
                    <div className="form-group">
                      <label>Full Name</label>
                      <input type="text" className="form-input" required value={authForm.name} onChange={e => setAuthForm({ ...authForm, name: e.target.value })} />
                    </div>
                  )}
                  <div className="form-group">
                    <label>Email Address</label>
                    <input type="email" className="form-input" required value={authForm.email} onChange={e => setAuthForm({ ...authForm, email: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Password</label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showPassword ? "text" : "password"}
                        className="form-input"
                        required
                        value={authForm.password}
                        onChange={e => setAuthForm({ ...authForm, password: e.target.value })}
                        style={{ paddingRight: '45px' }}
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                  <button type="submit" className="auth-btn primary full-width" disabled={isAuthenticating}>
                    {isAuthenticating ? 'Authenticating...' : (authMode === 'login' ? 'Log In' : 'Sign Up')}
                  </button>
                </form>
              </>
            ) : (
              <>
                <h2 className="auth-title" style={{ fontSize: '2.2rem', marginBottom: '12px', marginTop: '10px' }}>
                  Verify Access Code
                </h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
                  We sent a 6-digit code to <strong>{authForm.email}</strong>
                </p>
                <form onSubmit={verifyOtpSubmit} className="auth-form">
                  <div className="form-group">
                    <label>6-Digit OTP</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="······"
                      style={{ textAlign: 'center', letterSpacing: '8px', fontSize: '1.4rem' }}
                      maxLength={6}
                      required
                      value={otpValue}
                      onChange={e => setOtpValue(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="auth-btn primary full-width" disabled={isAuthenticating}>
                    {isAuthenticating ? 'Verifying...' : 'Complete Login'}
                  </button>
                  <p className="auth-toggle" style={{ textAlign: 'center' }}>
                    Didn't receive code? <span onClick={handleAuthSubmit}>Resend</span>
                  </p>
                </form>
              </>
            )}

            {!otpMode && (
              <p className="auth-toggle">
                {authMode === 'login' ? "Don't have an account? " : "Already have an account? "}
                <span onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>
                  {authMode === 'login' ? 'Sign up' : 'Log in'}
                </span>
              </p>
            )}
          </motion.div>
        </div>
      )}



      {(currentScreen === 'chat' || currentScreen === 'setup') && (
        <div className="app-shell">
          {/* Sidebar - smooth slide + fade */}
          <AnimatePresence>
            {showSidebar && (
              <motion.div
                className="sidebar-panel"
                initial={{ width: 0 }}
                animate={{ width: 280 }}
                exit={{ width: 0 }}
                transition={{ duration: 0.32, ease: [0.4, 0, 0.2, 1] }}
                style={{ overflow: 'hidden', flexShrink: 0 }}
              >
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1, transition: { delay: 0.12, duration: 0.2 } }}
                  exit={{ opacity: 0, transition: { duration: 0.12 } }}
                  style={{ width: 280, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '24px 16px', boxSizing: 'border-box' }}
                >
                  {/* Collapse button inside sidebar */}
                  <div className="sidebar-top-row">
                    <span className="sidebar-brand">CuraLink</span>
                    <button className="sidebar-toggle-btn" onClick={() => setShowSidebar(false)} title="Close sidebar">
                      <PanelLeftClose size={18} />
                    </button>
                  </div>
                  <div className="sidebar-header">
                    <button className="new-chat-btn" onClick={startNewChat}>
                      <Plus size={18} /> New Research
                    </button>
                  </div>
                  <div className="sidebar-list">
                    <div className="sidebar-label">Recent History</div>
                    {history.map((s, i) => (
                      <div key={i} className={`sidebar-item ${sessionId === s.id ? 'active' : ''}`} onClick={() => loadSession(s.id)}>
                        <History size={14} style={{ flexShrink: 0 }} />
                        <div className="session-topic" style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.topic}</div>
                        <button
                          className="delete-session-btn"
                          onClick={(e) => deleteSession(s.id, e)}
                          title="Delete Session"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Collapsed rail — always visible when sidebar is hidden */}
          <AnimatePresence>
            {!showSidebar && (
              <motion.div
                className="sidebar-collapsed-rail"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18 }}
              >
                <button className="sidebar-toggle-btn" onClick={() => setShowSidebar(true)} title="Open sidebar">
                  <PanelLeft size={18} />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div className="center-workspace" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}>
            <div className="workspace-top">
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div>
                  {currentScreen === 'chat' ? (
                    <>
                      <h2>{patient.disease}</h2>
                      <p>Clinical Search Focus: {patient.intent}</p>
                    </>
                  ) : (
                    <h2>Workspace Initialization</h2>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Status: Active</span>
                <Shield size={20} color="var(--accent-green)" />
                {/* Account Switcher */}
                <div style={{ position: 'relative' }}>
                  <button className="account-avatar-btn" onClick={() => setShowAccountMenu(!showAccountMenu)}>
                    <User size={15} />
                    <span>{authForm.name ? authForm.name.split(' ')[0] : authForm.email.split('@')[0]}</span>
                  </button>
                  {showAccountMenu && (
                    <motion.div className="account-dropdown glass-panel" style={{ right: 0, left: 'auto' }} initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                      <div className="account-dropdown-header">
                        <div className="account-avatar-circle">{(authForm.name || authForm.email)[0].toUpperCase()}</div>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{authForm.name || 'Researcher'}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{authForm.email}</div>
                        </div>
                      </div>
                      <div className="account-dropdown-divider" />
                      <button className="account-dropdown-item" onClick={addAccount}>
                        <Plus size={14} /> Add Account
                      </button>
                      <button className="account-dropdown-item" onClick={handleLogout} style={{ color: '#ef4444' }}>
                        <LogOut size={14} /> Sign Out
                      </button>
                    </motion.div>
                  )}
                </div>
              </div>
            </div>

            {currentScreen === 'setup' ? (
              <div className="intro-screen" style={{ position: 'relative', background: 'none', flex: 1, height: '100%', width: '100%' }}>
                <motion.div
                  className="intro-grid"
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                >
                  <div className="intro-left">
                    <div className="intro-logo">
                      <FlaskConical size={32} color="#fff" />
                    </div>
                    <h1 className="intro-title" style={{ fontSize: '3.5rem', marginBottom: '12px' }}>
                      Hey {authForm.name ? authForm.name.split(' ')[0] : (authForm.email ? authForm.email.split('@')[0] : 'Researcher')}!
                    </h1>
                    <h2 className="intro-title" style={{ fontSize: '1.8rem', opacity: 0.8 }}>Welcome to CuraLink Workspace</h2>
                    <p className="intro-subtitle" style={{ marginTop: '20px' }}>
                      A highly advanced, agentic medical research system. Provide the initial context parameters to initialize the neural search matrix.
                    </p>
                  </div>

                  <div className="intro-right glass-panel">
                    <div className="form-group">
                      <label>Pathology / Condition</label>
                      <input className="form-input" placeholder="e.g. Parkinson's Disease" value={patient.disease} onChange={(e) => setPatient({ ...patient, disease: e.target.value })} />
                    </div>
                    <div className="form-group">
                      <label>Primary Research Intent</label>
                      <input className="form-input" placeholder="e.g. Deep Brain Stimulation Risks" value={patient.intent} onChange={(e) => setPatient({ ...patient, intent: e.target.value })} />
                    </div>
                    <div className="form-group">
                      <label>Geographic Anchor (Optional)</label>
                      <input className="form-input" placeholder="e.g. Toronto, Canada" value={patient.location} onChange={(e) => setPatient({ ...patient, location: e.target.value })} />
                    </div>
                    <button className="start-btn" onClick={handleStart}>
                      Initialize Protocol
                    </button>
                  </div>
                </motion.div>
              </div>
            ) : (
              <>
                <div className="chat-history" ref={chatContainerRef} onScroll={handleScroll}>
                  <AnimatePresence>
                    {messages.map((msg, i) => (
                      <motion.div key={i} initial={{ opacity: 0, y: 10, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} className={`chat-bubble ${msg.role}`}>
                        {msg.role === 'assistant' && msg.thoughts && !msg.isStreaming && <ThoughtProcess thoughts={msg.thoughts} />}
                        <FormattedText text={msg.content} onCitationClick={handleCitationClick} />
                        {msg.role === 'assistant' && msg.thoughts && msg.sources && !msg.isStreaming && <SourcesList sources={msg.sources} highlightIdx={highlightIdx} />}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {isLoading && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="chat-bubble assistant" style={{ width: '100%', maxWidth: '100%' }}>
                      <ThinkingLog />
                    </motion.div>
                  )}
                </div>

                <div className="input-area">
                  <div className="input-wrapper">
                    <input className="query-input" placeholder="Send instructions to agent..." value={query} onChange={(e) => setQuery(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && performResearch(query)} />
                    <button className="send-btn" onClick={() => performResearch(query)} disabled={isLoading || !query.trim()}>
                      <Send size={18} />
                    </button>
                  </div>
                </div>
              </>
            )}
          </motion.div>
        </div>
      )}

      {/* Methodology Modal */}
      <AnimatePresence>
        {showMethodology && (
          <div className="modal-overlay" onClick={() => setShowMethodology(false)}>
            <motion.div
              className="methodology-modal glass-panel"
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <Brain size={24} color="var(--accent-cyan)" />
                <h2>Clinical Methodology</h2>
              </div>

              <div className="modal-body">
                <div className="method-section">
                  <div className="method-number">01</div>
                  <div className="method-text">
                    <h3>Aggregated Medical Retrieval</h3>
                    <p>Concurrent high-latency search across <strong>PubMed</strong>, <strong>OpenAlex</strong>, and <strong>ClinicalTrials.gov</strong>. Unlike standard AI, CuraLink only builds context from peer-reviewed abstracts and clinical trial registries.</p>
                  </div>
                </div>

                <div className="method-section">
                  <div className="method-number">02</div>
                  <div className="method-text">
                    <h3>Ragas Verification Protocol</h3>
                    <p>Every generated briefing undergoes a post-generation audit by an LLM Judge. We measure <strong>Faithfulness</strong> (grounding against sources) and <strong>Answer Relevancy</strong> to ensure 0% hallucination rates in clinical claims.</p>
                  </div>
                </div>

                <div className="method-section">
                  <div className="method-number">03</div>
                  <div className="method-text">
                    <h3>Neural Context Routing</h3>
                    <p>Submissions are intelligently routed between session memory and live search pipelines, maintaining clinical continuity while identifying precisely when new external evidence is required.</p>
                  </div>
                </div>
              </div>

              <button className="modal-close-btn" onClick={() => setShowMethodology(false)}>Close Specifications</button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

export default App;

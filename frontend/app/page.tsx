"use client";

import React, { useState, useEffect, useRef } from "react";

interface Source {
  source_document: string;
  section_title: string;
  collection: string;
}

interface Message {
  id: string;
  sender: "user" | "bot";
  text: string;
  retrievalType?: "hybrid_rag" | "sql_rag";
  sqlQuery?: string;
  sources?: Source[];
}

const DEMO_USERS = [
  { username: "dr.mehta", password: "doctor", displayName: "Dr. Mehta", role: "doctor", icon: "👨‍⚕️" },
  { username: "nurse.priya", password: "nurse", displayName: "Nurse Priya", role: "nurse", icon: "👩‍⚕️" },
  { username: "billing.ravi", password: "billing_executive", displayName: "Billing Ravi", role: "billing_executive", icon: "💼" },
  { username: "tech.anand", password: "technician", displayName: "Tech Anand", role: "technician", icon: "🔧" },
  { username: "admin.sys", password: "admin", displayName: "System Admin", role: "admin", icon: "👑" },
];

const API_BASE = "http://localhost:8000";

export default function Home() {
  // Authentication & Session State
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(false);

  // Chat & UI State
  const [collections, setCollections] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  
  // Ref for auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("medibot_token");
    const savedRole = localStorage.getItem("medibot_role");
    const savedName = localStorage.getItem("medibot_display_name");
    
    if (savedToken && savedRole && savedName) {
      setToken(savedToken);
      setRole(savedRole);
      setDisplayName(savedName);
      fetchCollections(savedToken);
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loadingChat]);

  // Fetch collections list for the current role
  const fetchCollections = async (authToken: string) => {
    try {
      const res = await fetch(`${API_BASE}/collections`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCollections(data.collections || []);
      }
    } catch (err) {
      console.error("Failed to fetch collections", err);
    }
  };

  // Login handler (JSON payload)
  const handleLogin = async (e?: React.FormEvent, customCreds?: typeof DEMO_USERS[0]) => {
    if (e) e.preventDefault();
    
    setError(null);
    setLoadingAuth(true);

    const loginUser = customCreds ? customCreds.username : username;
    const loginPass = customCreds ? customCreds.password : password;
    const resolvedName = customCreds ? customCreds.displayName : loginUser;

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginUser, password: loginPass }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Authentication failed");
      }

      const data = await res.json();
      
      // Save credentials & update state
      localStorage.setItem("medibot_token", data.access_token);
      localStorage.setItem("medibot_role", data.role);
      localStorage.setItem("medibot_display_name", resolvedName);

      setToken(data.access_token);
      setRole(data.role);
      setDisplayName(resolvedName);
      setError(null);
      
      // Fetch collections
      await fetchCollections(data.access_token);
      
      // Seed default welcome message
      setMessages([
        {
          id: "welcome",
          sender: "bot",
          text: `Hello ${resolvedName}! You are logged in as a **${data.role.replace("_", " ")}**. 
You have authorized access to search documents in the collections: **${(ROLE_ACCESS_LABELS[data.role] || []).join(", ")}**.
How can I assist you today?`,
        },
      ]);
    } catch (err: any) {
      setError(err.message || "Something went wrong. Ensure the backend server is running.");
    } finally {
      setLoadingAuth(false);
    }
  };

  // Logout handler
  const handleLogout = () => {
    localStorage.removeItem("medibot_token");
    localStorage.removeItem("medibot_role");
    localStorage.removeItem("medibot_display_name");
    setToken(null);
    setRole(null);
    setDisplayName("");
    setCollections([]);
    setMessages([]);
    setUsername("");
    setPassword("");
  };

  // Send message handler
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !token || loadingChat) return;

    const userText = inputMessage.trim();
    setInputMessage("");
    setError(null);

    // Add user message to state
    const userMsg: Message = {
      id: Math.random().toString(),
      sender: "user",
      text: userText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoadingChat(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: userText }),
      });

      if (!res.ok) {
        if (res.status === 401) {
          handleLogout();
          throw new Error("Session expired. Please log in again.");
        }
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to fetch response");
      }

      const data = await res.json();

      const botMsg: Message = {
        id: Math.random().toString(),
        sender: "bot",
        text: data.answer,
        retrievalType: data.retrieval_type,
        sqlQuery: data.sql_query,
        sources: data.sources,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: Math.random().toString(),
        sender: "bot",
        text: `⚠️ **Error:** ${err.message || "Failed to retrieve answer. Please make sure the API server is online."}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoadingChat(false);
    }
  };

  // Map roles to human-friendly collection names
  const ROLE_ACCESS_LABELS: Record<string, string[]> = {
    doctor: ["General FAQs", "Clinical Protocols", "Nursing Manuals"],
    nurse: ["General FAQs", "Nursing Manuals"],
    billing_executive: ["General FAQs", "Billing Guides"],
    technician: ["General FAQs", "Equipment Manuals"],
    admin: ["General FAQs", "Clinical Protocols", "Nursing Manuals", "Billing Guides", "Equipment Manuals"],
  };

  const getRoleBadgeColor = (roleStr: string) => {
    switch (roleStr) {
      case "admin": return "bg-red-500/20 text-red-300 border-red-500/30";
      case "doctor": return "bg-teal-500/20 text-teal-300 border-teal-500/30";
      case "nurse": return "bg-purple-500/20 text-purple-300 border-purple-500/30";
      case "billing_executive": return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "technician": return "bg-blue-500/20 text-blue-300 border-blue-500/30";
      default: return "bg-zinc-500/20 text-zinc-300 border-zinc-500/30";
    }
  };

  // Login Screen
  if (!token) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-50 relative overflow-hidden px-4">
        {/* Glow Effects */}
        <div className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-violet-600/10 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-teal-600/10 blur-[120px] pointer-events-none" />

        <div className="w-full max-w-lg bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-8 backdrop-blur-xl shadow-2xl transition-all duration-300">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-violet-600 to-teal-400 p-[1.5px] shadow-lg mb-4">
              <div className="w-full h-full bg-zinc-950 rounded-[15px] flex items-center justify-center text-3xl">
                🩺
              </div>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-zinc-50 via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
              MediBot Portal
            </h1>
            <p className="text-zinc-500 mt-2 text-sm">
              Secure Role-Based Hybrid RAG & database assistant.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-950/30 border border-red-500/20 text-red-300 rounded-xl text-xs flex items-center gap-2">
              <span>⚠️</span>
              <p>{error}</p>
            </div>
          )}

          {/* Quick Login Accounts */}
          <div className="mb-8">
            <h3 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-3">
              Quick Connect (Demo Accounts)
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {DEMO_USERS.map((user) => (
                <button
                  key={user.username}
                  onClick={() => handleLogin(undefined, user)}
                  disabled={loadingAuth}
                  className="flex flex-col items-center justify-center p-3 rounded-xl bg-zinc-900/50 hover:bg-zinc-800/60 border border-zinc-800 hover:border-zinc-700/80 active:scale-95 transition-all text-center group"
                >
                  <span className="text-2xl mb-1 group-hover:scale-110 transition-transform duration-200">{user.icon}</span>
                  <span className="text-xs font-medium text-zinc-300">{user.displayName}</span>
                  <span className="text-[10px] text-zinc-500 mt-0.5 capitalize">{user.role.replace("_", " ")}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="relative flex py-2 items-center mb-6">
            <div className="flex-grow border-t border-zinc-800/80"></div>
            <span className="flex-shrink mx-4 text-zinc-600 text-xs uppercase font-medium">Or Use Custom credentials</span>
            <div className="flex-grow border-t border-zinc-800/80"></div>
          </div>

          {/* Regular Login Form */}
          <form onSubmit={(e) => handleLogin(e)} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. dr.mehta"
                required
                className="w-full px-4 py-2.5 rounded-xl bg-zinc-950/80 border border-zinc-800 focus:border-zinc-700 focus:ring-1 focus:ring-zinc-700 outline-none text-sm text-zinc-300 placeholder-zinc-700 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full px-4 py-2.5 rounded-xl bg-zinc-950/80 border border-zinc-800 focus:border-zinc-700 focus:ring-1 focus:ring-zinc-700 outline-none text-sm text-zinc-300 placeholder-zinc-700 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loadingAuth}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-teal-500 hover:from-violet-500 hover:to-teal-400 text-white font-medium text-sm transition-all shadow-md active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
            >
              {loadingAuth ? (
                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                "Log In"
              )}
            </button>
          </form>
        </div>
      </main>
    );
  }

  // Chat Screen
  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden relative font-sans">
      {/* Background soft glowing blur blobs */}
      <div className="absolute top-[-30%] right-[-10%] w-[60vw] h-[60vw] rounded-full bg-teal-600/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-30%] left-[-10%] w-[60vw] h-[60vw] rounded-full bg-violet-600/5 blur-[120px] pointer-events-none" />

      {/* Sidebar Panel */}
      <aside className="w-80 border-r border-zinc-900 bg-zinc-950/80 backdrop-blur-xl flex flex-col justify-between z-10">
        <div className="flex flex-col h-full overflow-hidden">
          {/* Brand header */}
          <div className="p-6 border-b border-zinc-900 flex items-center gap-3">
            <span className="text-2xl">🩺</span>
            <div>
              <h2 className="font-extrabold text-sm tracking-wide bg-gradient-to-r from-zinc-50 to-zinc-400 bg-clip-text text-transparent">
                MEDIBOT CONSOLE
              </h2>
              <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">
                Authorized System v1.0
              </p>
            </div>
          </div>

          {/* User profile details */}
          <div className="p-6 border-b border-zinc-900 bg-zinc-900/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-xl">
                {role === "doctor" ? "👨‍⚕️" : role === "nurse" ? "👩‍⚕️" : role === "billing_executive" ? "💼" : role === "technician" ? "🔧" : "👑"}
              </div>
              <div className="overflow-hidden">
                <h3 className="font-semibold text-sm text-zinc-200 truncate">{displayName}</h3>
                <span className={`inline-block border rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide mt-1 capitalize ${getRoleBadgeColor(role || "")}`}>
                  {role?.replace("_", " ")}
                </span>
              </div>
            </div>

            {/* Document Collection List */}
            <div>
              <h4 className="text-zinc-500 text-[10px] font-bold uppercase tracking-wider mb-2">
                Accessible Document Collections
              </h4>
              <div className="space-y-1">
                {(ROLE_ACCESS_LABELS[role || ""] || []).map((colName) => (
                  <div
                    key={colName}
                    className="flex items-center gap-2 text-xs font-medium text-zinc-400 bg-zinc-900/30 border border-zinc-900/60 rounded-lg px-3 py-2"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
                    <span>{colName}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Interactive Info Block */}
          <div className="p-6 text-xs text-zinc-500 space-y-3 flex-1 overflow-y-auto">
            <div>
              <h5 className="font-bold text-zinc-400 text-[10px] uppercase mb-1">Vector DB (Qdrant)</h5>
              <p className="text-[10.5px]">Connected: 12 Clinical & Administrative Guides (Hybrid dense/sparse indexed).</p>
            </div>
            <div>
              <h5 className="font-bold text-zinc-400 text-[10px] uppercase mb-1">Relational DB (SQLite)</h5>
              <p className="text-[10.5px]">Connected: 85 Claims, 78 Equipment Maintenance Tickets (Read-only SELECT enforce).</p>
            </div>
            <div>
              <h5 className="font-bold text-zinc-400 text-[10px] uppercase mb-1">Rerank Engine</h5>
              <p className="text-[10.5px]">Ms-Marco MiniLM-L6 CrossEncoder (top-3 rerank output).</p>
            </div>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-zinc-900">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-zinc-800 hover:border-red-500/20 bg-zinc-900/20 hover:bg-red-950/10 text-zinc-400 hover:text-red-300 text-xs font-medium transition-all"
          >
            <span>🚪</span>
            <span>Disconnect Session</span>
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col justify-between bg-zinc-950/20 z-10 relative">
        {/* Chat Header */}
        <header className="h-[73px] border-b border-zinc-900 px-8 flex items-center justify-between bg-zinc-950/40 backdrop-blur-xl">
          <div>
            <h2 className="font-bold text-sm text-zinc-200">MediBot Assistant</h2>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider">Secure Channel Active</span>
            </div>
          </div>

          <div className="text-zinc-500 text-xs">
            Host: <span className="text-zinc-400 font-mono text-[10.5px]">localhost:8000</span>
          </div>
        </header>

        {/* Messages Body */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          {messages.map((msg) => {
            const isUser = msg.sender === "user";
            return (
              <div
                key={msg.id}
                className={`flex ${isUser ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-2xl rounded-2xl p-5 border text-sm transition-all duration-300 leading-relaxed shadow-md
                    ${
                      isUser
                        ? "bg-violet-600/15 border-violet-500/20 text-violet-100 rounded-tr-none"
                        : "bg-zinc-900/40 border-zinc-800/70 text-zinc-300 rounded-tl-none backdrop-blur-sm"
                    }`}
                >
                  {/* Message content text */}
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {/* Retrieval tags / pills (for Bot messages only) */}
                  {!isUser && msg.retrievalType && (
                    <div className="mt-4 pt-3 border-t border-zinc-800/80 flex flex-wrap gap-2 items-center">
                      <span className={`px-2.5 py-0.5 text-[9px] font-bold rounded-full uppercase tracking-wider border
                        ${
                          msg.retrievalType === "sql_rag"
                            ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
                            : "bg-blue-500/10 text-blue-300 border-blue-500/20"
                        }`}
                      >
                        {msg.retrievalType === "sql_rag" ? "📊 SQL RAG" : "📄 Hybrid RAG"}
                      </span>

                      {/* Display SQL queries */}
                      {msg.sqlQuery && (
                        <details className="w-full mt-2 cursor-pointer group">
                          <summary className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide group-open:text-emerald-300 transition-colors">
                            Inspect Executed SQL Query
                          </summary>
                          <div className="mt-2 p-3 bg-zinc-950 border border-zinc-900 rounded-lg font-mono text-xs text-emerald-400 overflow-x-auto select-all">
                            {msg.sqlQuery}
                          </div>
                        </details>
                      )}

                      {/* Display source citations */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="w-full mt-2 space-y-1">
                          <span className="text-[9.5px] font-bold text-zinc-500 uppercase tracking-wide block">
                            Document Citations
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.sources.map((src, sIdx) => (
                              <div
                                key={sIdx}
                                className="inline-flex items-center gap-1.5 px-2 py-1 bg-zinc-950/60 border border-zinc-900 rounded-md text-[10.5px] text-zinc-400"
                              >
                                <span>📄</span>
                                <span className="font-semibold text-zinc-300">{src.source_document}</span>
                                <span className="text-zinc-600">|</span>
                                <span className="text-zinc-400 italic">{src.section_title}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Loading status card */}
          {loadingChat && (
            <div className="flex justify-start">
              <div className="max-w-md rounded-2xl rounded-tl-none p-5 bg-zinc-900/20 border border-zinc-800/40 backdrop-blur-sm shadow-md flex items-center gap-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-teal-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 rounded-full bg-teal-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 rounded-full bg-teal-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Generating answer...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Footer Form */}
        <form onSubmit={handleSendMessage} className="p-8 bg-gradient-to-t from-zinc-950 via-zinc-950 to-transparent">
          <div className="max-w-3xl mx-auto relative flex items-center">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Ask a question (e.g. "${
                role === "doctor" || role === "admin" 
                  ? "What are ICU nurse precautions?" 
                  : role === "billing_executive" 
                    ? "How many claims are pending?" 
                    : "Ask about manual or guidelines..."
              }")`}
              disabled={loadingChat}
              className="w-full px-6 py-4 pr-16 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 focus:border-zinc-700/80 focus:ring-1 focus:ring-zinc-700 outline-none text-sm text-zinc-200 placeholder-zinc-600 backdrop-blur-xl shadow-xl transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || loadingChat}
              className="absolute right-3 p-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium transition-all shadow-md active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
            >
              <svg className="w-4 h-4 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9-2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
            </button>
          </div>
          <p className="text-center text-[10px] text-zinc-600 mt-3 font-medium uppercase tracking-wider">
            RBAC Rules Active • Data Transmission Encrypted
          </p>
        </form>
      </main>
    </div>
  );
}

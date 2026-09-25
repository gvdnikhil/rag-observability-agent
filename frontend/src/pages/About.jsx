import { Link } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";

export default function About() {
  return (
    <div className="app-shell">
      <div className="bg-glow" />
      <header className="app-header enter">
        <div>
          <h1>Case File: How This Works</h1>
          <p className="subtitle">The full record — what these agents do, and why the answers can be trusted (or refused).</p>
          <Link className="nav-link" to="/">← Nimbus demo</Link>
          <Link className="nav-link" to="/resume">Chat with your resume →</Link>
        </div>
        <ThemeToggle />
      </header>

      <div className="about-page enter">
        <h2>What this is</h2>
        <p>
          Two small agents that answer questions from documents — and, unlike most chatbot demos, show their
          work. Every answer comes with a trace: what was retrieved, how confident the match was, which tools
          were called, how long it took, how many tokens it cost, and whether a guardrail let the answer
          through at all.
        </p>

        <h2>The two case files</h2>
        <p>
          <strong>Nimbus RAG Assistant</strong> answers from a fixed sample knowledge base — a fictional
          product's docs. <strong>Chat With Your Resume</strong> answers from whatever resume you upload,
          scoped only to your browser session.
        </p>

        <h2>How an answer gets made</h2>
        <p>
          The agent (built on <code>LangGraph</code>) decides whether it needs to search before answering,
          and can search more than once if the first attempt wasn't enough. Retrieval runs against a local
          vector index (<code>FAISS</code> + <code>sentence-transformers</code> embeddings — no external API,
          no cost). A guardrail then checks the evidence behind the answer before it ships: if nothing
          relevant was found, or the match is too weak, the agent refuses instead of guessing.
        </p>

        <h2>Why the resume agent forgets you</h2>
        <p>
          Your resume and the conversation about it live only in server memory, scoped to your browser
          session. Nothing touches disk. A background sweep clears idle sessions automatically, and a
          "Clear my data" button clears it immediately on request. Close the tab, and the session id
          disappears with it.
        </p>

        <h2>What's actually running underneath</h2>
        <ul>
          <li>FastAPI backends, one independently-deployed microservice per case file</li>
          <li>LangGraph for the agent loop, with a <code>MemorySaver</code> checkpointer for the resume agent's conversation memory</li>
          <li>FAISS + sentence-transformers for retrieval, entirely local, no embedding API cost</li>
          <li>A configurable LLM provider layer — Groq by default (free tier), swappable to OpenAI or Gemini via one env var</li>
          <li>React + Vite frontend, deployed on Vercel; backends on Railway</li>
        </ul>

        <h2>Source</h2>
        <p>
          Full code, including the trace/guardrail logic itself, is public:{" "}
          <a href="https://github.com/gvdnikhil/rag-observability-agent" target="_blank" rel="noreferrer">
            github.com/gvdnikhil/rag-observability-agent
          </a>
        </p>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  clearSession,
  getSessionStatus,
  sendResumeChat,
  uploadResumePdf,
  uploadResumeText,
} from "../lib/resumeApi";
import ChatPanel from "../components/ChatPanel";
import StatusDot from "../components/StatusDot";
import ThemeToggle from "../components/ThemeToggle";
import TracePanel from "../components/TracePanel";

const BUSY_STAGES = [
  { at: 0, label: "thinking", status: "thinking" },
  { at: 500, label: "searching your resume…", status: "searching" },
  { at: 1800, label: "checking guardrails…", status: "guardrail" },
];

function UploadScreen({ onUploaded }) {
  const [mode, setMode] = useState("pdf");
  const [pastedText, setPastedText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  async function handleFile(file) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const result = await uploadResumePdf(file);
      onUploaded(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handlePasteSubmit(e) {
    e.preventDefault();
    if (!pastedText.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await uploadResumeText(pastedText.trim());
      onUploaded(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="upload-screen enter">
      <div className="upload-card">
        <h2>Upload your resume</h2>
        <p className="upload-note">
          Nothing is saved to disk — it's embedded in memory for this browser tab only, and gone when
          the tab closes, the session goes idle, or you hit "Clear my data".
        </p>

        <div className="upload-tabs">
          <button className={mode === "pdf" ? "active" : ""} onClick={() => setMode("pdf")} type="button">
            PDF
          </button>
          <button className={mode === "text" ? "active" : ""} onClick={() => setMode("text")} type="button">
            Paste text
          </button>
        </div>

        {mode === "pdf" ? (
          <div
            className="dropzone"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              handleFile(e.dataTransfer.files?.[0]);
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              hidden
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
            {busy ? "Uploading…" : "Click or drop a PDF here"}
          </div>
        ) : (
          <form onSubmit={handlePasteSubmit} className="paste-form">
            <textarea
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="Paste your resume text here…"
              rows={8}
            />
            <button type="submit" disabled={busy || !pastedText.trim()}>
              {busy ? "Uploading…" : "Use this text"}
            </button>
          </form>
        )}

        {error && <p className="upload-error">{error}</p>}
      </div>
    </div>
  );
}

export default function ResumeChat() {
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [hasResume, setHasResume] = useState(false);
  const [messages, setMessages] = useState([]);
  const [trace, setTrace] = useState(null);
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState("thinking");
  const [status, setStatus] = useState("idle");
  const timers = useRef([]);

  useEffect(() => {
    getSessionStatus()
      .then((s) => setHasResume(s.has_resume))
      .catch(() => setHasResume(false))
      .finally(() => setLoadingStatus(false));
  }, []);

  function startBusyStages() {
    timers.current.forEach(clearTimeout);
    timers.current = BUSY_STAGES.map((stage) =>
      setTimeout(() => {
        setBusyLabel(stage.label);
        setStatus(stage.status);
      }, stage.at)
    );
  }

  function stopBusyStages() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }

  async function handleSend(text) {
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    startBusyStages();

    try {
      const data = await sendResumeChat(text);
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
      setTrace(data.trace);
      setSummary(data.summary);
      setStatus("done");
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: `Something went wrong: ${err.message}` }]);
      setStatus("error");
    } finally {
      stopBusyStages();
      setBusy(false);
      setTimeout(() => setStatus("idle"), 1500);
    }
  }

  async function handleClear() {
    await clearSession().catch(() => {});
    setHasResume(false);
    setMessages([]);
    setTrace(null);
    setSummary(null);
  }

  return (
    <div className="app-shell">
      <div className="bg-glow" />
      <header className="app-header enter">
        <div>
          <h1>Chat With Your Resume</h1>
          <p className="subtitle">Upload your resume, ask about it — ephemeral, gone when your session ends.</p>
          <Link className="nav-link" to="/">← Back to Nimbus demo</Link>
          <Link className="nav-link" to="/about">About / how it works →</Link>
        </div>
        <div className="header-actions">
          {hasResume && (
            <button className="clear-btn" onClick={handleClear} type="button">
              Clear my data
            </button>
          )}
          <StatusDot status={status} />
          <ThemeToggle />
        </div>
      </header>

      {loadingStatus ? null : !hasResume ? (
        <UploadScreen onUploaded={() => setHasResume(true)} />
      ) : (
        <main className="app-main">
          <ChatPanel
            messages={messages}
            onSend={handleSend}
            busy={busy}
            busyLabel={busyLabel}
            placeholder="Ask about this resume…"
            emptyHint={
              <>
                Ask something like <em>"What was their most recent role?"</em> or{" "}
                <em>"What's the capital of France?"</em> to see the guardrail refuse an unrelated question.
              </>
            }
          />
          <TracePanel trace={trace} summary={summary} busy={busy} />
        </main>
      )}
    </div>
  );
}

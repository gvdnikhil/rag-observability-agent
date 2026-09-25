import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { sendMessage } from "../api";
import ChatPanel from "../components/ChatPanel";
import StatusDot from "../components/StatusDot";
import TracePanel from "../components/TracePanel";

const BUSY_STAGES = [
  { at: 0, label: "thinking", status: "thinking" },
  { at: 500, label: "searching knowledge base…", status: "searching" },
  { at: 1800, label: "checking guardrails…", status: "guardrail" },
];

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [trace, setTrace] = useState(null);
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState("thinking");
  const [status, setStatus] = useState("idle");
  const timers = useRef([]);

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
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    startBusyStages();

    try {
      const data = await sendMessage(text, history);
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

  return (
    <div className="app-shell">
      <div className="bg-glow" />
      <header className="app-header enter">
        <div>
          <h1>Nimbus RAG Assistant</h1>
          <p className="subtitle">An agent that shows its work — retrieval, tool calls, cost, and guardrails, live.</p>
          <Link className="nav-link" to="/resume">Try it on your own resume →</Link>
        </div>
        <StatusDot status={status} />
      </header>

      <main className="app-main">
        <ChatPanel messages={messages} onSend={handleSend} busy={busy} busyLabel={busyLabel} />
        <TracePanel trace={trace} summary={summary} busy={busy} />
      </main>
    </div>
  );
}

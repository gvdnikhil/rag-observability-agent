const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function sendMessage(message, history) {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

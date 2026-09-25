import { fetchWithSession } from "./session";

const API_URL = import.meta.env.VITE_RESUME_API_URL || "http://localhost:8001";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function getSessionStatus() {
  return fetchWithSession(`${API_URL}/api/session`).then(handle);
}

export function clearSession() {
  return fetchWithSession(`${API_URL}/api/session`, { method: "DELETE" }).then(handle);
}

export function uploadResumePdf(file) {
  const form = new FormData();
  form.append("file", file);
  return fetchWithSession(`${API_URL}/api/resume/pdf`, { method: "POST", body: form }).then(handle);
}

export function uploadResumeText(text) {
  return fetchWithSession(`${API_URL}/api/resume/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }).then(handle);
}

export function sendResumeChat(message) {
  return fetchWithSession(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  }).then(handle);
}

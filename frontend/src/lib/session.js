const STORAGE_KEY = "resume-agent-session-id";

export function getSessionId() {
  let id = sessionStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}

export function resetSessionId() {
  sessionStorage.removeItem(STORAGE_KEY);
  return getSessionId();
}

export function fetchWithSession(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: { ...options.headers, "X-Session-Id": getSessionId() },
  });
}

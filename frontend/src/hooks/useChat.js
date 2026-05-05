import { useSimStore } from "../store/simStore";

export function useChat() {
  const backendUrl = useSimStore((s) => s.backendUrl);
  const chatSessionId = useSimStore((s) => s.chatSessionId);
  const addChatMessage = useSimStore((s) => s.addChatMessage);
  const setChatSessionId = useSimStore((s) => s.setChatSessionId);
  const setChatting = useSimStore((s) => s.setChatting);
  const setApiError = useSimStore((s) => s.setApiError);

  async function sendMessage(text) {
    if (!text.trim()) return;
    addChatMessage({ role: "user", text });
    setChatting(true);
    setApiError("");
    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: chatSessionId, top_k: 4 })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail || data));
      }
      if (data.session_id && data.session_id !== chatSessionId) {
        setChatSessionId(data.session_id);
      }
      addChatMessage({ role: "assistant", text: data.answer, sources: data.context_sources || [] });
    } catch (error) {
      setApiError(error.message || "Chat failed");
      addChatMessage({ role: "assistant", text: "I hit an error while answering. Please retry." });
    } finally {
      setChatting(false);
    }
  }

  return { sendMessage };
}

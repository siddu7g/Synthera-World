import { useState } from "react";
import { useChat } from "../../hooks/useChat";
import { useSimStore } from "../../store/simStore";

export default function ChatPanel() {
  const [input, setInput] = useState("");
  const { sendMessage } = useChat();
  const chatMessages = useSimStore((s) => s.chatMessages);
  const chatSessionId = useSimStore((s) => s.chatSessionId);
  const isChatting = useSimStore((s) => s.isChatting);
  const clearChatMessages = useSimStore((s) => s.clearChatMessages);

  async function onSend() {
    const text = input.trim();
    if (!text) return;
    setInput("");
    await sendMessage(text);
  }

  return (
    <div className="panel">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="panel-title mb-0">RAG Chat</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Session: {chatSessionId}</span>
          <button className="badge" onClick={clearChatMessages} type="button">
            Clear
          </button>
        </div>
      </div>
      <div className="mb-2 max-h-56 overflow-auto rounded-lg border border-slate-800 bg-slate-950/60 p-2 text-xs">
        {!chatMessages.length && <div className="text-slate-400">Ask about robots, APIs, setup, or prior context.</div>}
        {chatMessages.map((m, i) => (
          <div key={`${m.role}-${i}`} className="mb-2">
            <div className={`font-semibold ${m.role === "user" ? "text-indigo-300" : "text-emerald-300"}`}>
              {m.role === "user" ? "You" : "Synthera"}
            </div>
            <div className="whitespace-pre-wrap text-slate-200">{m.text}</div>
            {m.sources?.length ? (
              <div className="mt-1 text-[11px] text-slate-400">Sources: {m.sources.join(", ")}</div>
            ) : null}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="input"
          placeholder="Ask a context-aware question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSend();
          }}
        />
        <button className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium disabled:opacity-50" onClick={onSend} disabled={isChatting}>
          {isChatting ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

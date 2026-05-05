import { useState } from "react";
import { useGenerate } from "../../hooks/useGenerate";
import { useSimulate } from "../../hooks/useSimulate";
import { useChat } from "../../hooks/useChat";
import { useSimStore } from "../../store/simStore";

export default function PromptWorkspace() {
  const [chatInput, setChatInput] = useState("");
  const { generate } = useGenerate();
  const { run, stop } = useSimulate();
  const { sendMessage } = useChat();

  const task = useSimStore((s) => s.config.task);
  const setNested = useSimStore((s) => s.setNested);
  const generationId = useSimStore((s) => s.generationId);
  const isGenerating = useSimStore((s) => s.isGenerating);
  const isSimulating = useSimStore((s) => s.isSimulating);
  const isChatting = useSimStore((s) => s.isChatting);
  const chatMessages = useSimStore((s) => s.chatMessages);
  const clearChatMessages = useSimStore((s) => s.clearChatMessages);

  async function onSendChat() {
    const text = chatInput.trim();
    if (!text) return;
    setChatInput("");
    await sendMessage(text);
  }

  return (
    <div className="panel space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="panel-title mb-0">Prompt Workspace</h2>
        <span className="text-xs text-slate-400">
          {generationId ? `Generation: ${generationId.slice(0, 10)}...` : "No generation yet"}
        </span>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-400">
          Simulation Prompt
        </label>
        <textarea
          className="input min-h-24"
          value={task.description}
          onChange={(e) => setNested("task", { description: e.target.value })}
          placeholder="Describe the robot behavior to generate..."
        />
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">Duration: {task.duration_seconds}s</span>
          <div className="flex gap-2">
            <button className="badge" onClick={() => setNested("task", { description: "stand still for the full duration" })} type="button">
              Stand
            </button>
            <button className="badge" onClick={() => setNested("task", { description: "walk forward 5 steps and stop" })} type="button">
              Move 5 Steps
            </button>
          </div>
        </div>
        <input
          type="range"
          min={10}
          max={120}
          value={task.duration_seconds}
          onChange={(e) => setNested("task", { duration_seconds: Number(e.target.value) })}
          className="w-full"
        />
      </div>

      <div className="grid grid-cols-3 gap-2">
        <button
          className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium disabled:opacity-50"
          onClick={() => generate().catch(() => {})}
          disabled={isGenerating}
        >
          {isGenerating ? "Generating..." : "Generate"}
        </button>
        <button
          className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium disabled:opacity-50"
          onClick={() => run().catch(() => {})}
          disabled={isSimulating || !generationId}
        >
          {isSimulating ? "Running..." : "Run"}
        </button>
        <button className="rounded-lg bg-rose-600 px-3 py-2 text-sm font-medium" onClick={() => stop()}>
          Stop
        </button>
      </div>

      <div className="border-t border-slate-800 pt-3">
        <div className="mb-2 flex items-center justify-between">
          <label className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Assistant Chat (RAG + Memory)
          </label>
          <button className="badge" onClick={clearChatMessages} type="button">
            Clear
          </button>
        </div>
        <div className="mb-2 max-h-48 overflow-auto rounded-lg border border-slate-800 bg-slate-950/60 p-2 text-xs">
          {!chatMessages.length && <div className="text-slate-400">Ask follow-ups or clarifications before generating.</div>}
          {chatMessages.map((m, i) => (
            <div key={`${m.role}-${i}`} className="mb-2">
              <div className={`font-semibold ${m.role === "user" ? "text-indigo-300" : "text-emerald-300"}`}>
                {m.role === "user" ? "You" : "Synthera"}
              </div>
              <div className="whitespace-pre-wrap text-slate-200">{m.text}</div>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            className="input"
            placeholder="Ask assistant about context, errors, or strategy..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onSendChat();
            }}
          />
          <button
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium disabled:opacity-50"
            onClick={onSendChat}
            disabled={isChatting}
          >
            {isChatting ? "..." : "Ask"}
          </button>
        </div>
      </div>
    </div>
  );
}

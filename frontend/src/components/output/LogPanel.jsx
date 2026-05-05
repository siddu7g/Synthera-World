import { useSimStore } from "../../store/simStore";

export default function LogPanel() {
  const logs = useSimStore((s) => s.logs);
  const clearLogs = useSimStore((s) => s.clearLogs);

  return (
    <div className="panel">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="panel-title mb-0">Live Logs</h2>
        <button className="badge" onClick={clearLogs} type="button">
          Clear
        </button>
      </div>
      <pre className="max-h-80 overflow-auto rounded-lg border border-slate-800 bg-slate-950/60 p-3 whitespace-pre-wrap text-xs">
        {logs.length ? logs.join("\n") : "No logs yet."}
      </pre>
    </div>
  );
}

import { useEffect } from "react";
import { useSimStore } from "../../store/simStore";

export default function HistoryPanel() {
  const backendUrl = useSimStore((s) => s.backendUrl);
  const history = useSimStore((s) => s.history);
  const setHistory = useSimStore((s) => s.setHistory);

  useEffect(() => {
    fetch(`${backendUrl}/simulations`)
      .then((res) => res.json())
      .then((data) => setHistory(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, [backendUrl, setHistory]);

  return (
    <div className="panel">
      <h2 className="panel-title">History</h2>
      <div className="max-h-72 overflow-auto space-y-2 text-xs">
        {history.map((item) => (
          <div key={item.generation_id} className="rounded-lg border border-slate-800 bg-slate-950/40 p-2">
            <div className="font-medium">{item.robot_name || item.generation_id}</div>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-slate-400">{item.generation_id.slice(0, 10)}...</span>
              <span
                className={`badge ${
                  item.status === "complete"
                    ? "border-emerald-500/50 text-emerald-300"
                    : item.status === "failed"
                    ? "border-rose-500/50 text-rose-300"
                    : ""
                }`}
              >
                {item.status}
              </span>
            </div>
          </div>
        ))}
        {!history.length && <div className="text-slate-400">No runs yet.</div>}
      </div>
    </div>
  );
}

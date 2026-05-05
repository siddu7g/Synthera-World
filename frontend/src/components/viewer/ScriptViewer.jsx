import { useSimStore } from "../../store/simStore";

export default function ScriptViewer() {
  const script = useSimStore((s) => s.generatedScript);
  const generationId = useSimStore((s) => s.generationId);

  return (
    <div className="panel">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="panel-title mb-0">Generated Script</h2>
        <span className="text-xs text-slate-400">{generationId || "-"}</span>
      </div>
      <pre className="max-h-80 overflow-auto rounded-lg border border-slate-800 bg-slate-950/60 p-3 whitespace-pre-wrap text-xs">
        {script || "No script yet."}
      </pre>
    </div>
  );
}

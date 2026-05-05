import { useSimStore } from "../../store/simStore";

export default function TopBar() {
  const generationId = useSimStore((s) => s.generationId);
  const apiNotice = useSimStore((s) => s.apiNotice);
  const apiError = useSimStore((s) => s.apiError);

  return (
    <div className="panel space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Synthera World</h1>
          <p className="text-sm text-slate-400">Configure. Generate. Simulate.</p>
        </div>
        <div className="text-right">
          <div className="badge">Beta v0</div>
          <div className="mt-1 text-xs text-slate-400">
            {generationId ? `Last ID: ${generationId.slice(0, 8)}...` : "No generation yet"}
          </div>
        </div>
      </div>
      <div
        className={`rounded-lg border px-3 py-2 text-sm ${
          apiError
            ? "border-rose-500/40 bg-rose-900/30 text-rose-200"
            : "border-emerald-500/30 bg-emerald-900/20 text-emerald-200"
        }`}
      >
        {apiError || apiNotice}
      </div>
    </div>
  );
}

import { useGenerate } from "../../hooks/useGenerate";
import { useSimulate } from "../../hooks/useSimulate";
import { useSimStore } from "../../store/simStore";

export default function SimControls() {
  const { generate } = useGenerate();
  const { run, stop } = useSimulate();
  const isGenerating = useSimStore((s) => s.isGenerating);
  const isSimulating = useSimStore((s) => s.isSimulating);
  const generationId = useSimStore((s) => s.generationId);

  return (
    <div className="panel space-y-3">
      <h2 className="panel-title">Simulation Controls</h2>
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
      {!generationId && <div className="text-xs text-amber-300">Generate first to enable Run.</div>}
    </div>
  );
}

import { useSimStore } from "../../store/simStore";

export default function TaskPanel() {
  const task = useSimStore((s) => s.config.task);
  const setNested = useSimStore((s) => s.setNested);

  return (
    <div className="panel space-y-3">
      <h2 className="panel-title">Task</h2>
      <textarea
        className="input"
        rows={3}
        value={task.description}
        onChange={(e) => setNested("task", { description: e.target.value })}
      />
      <input
        type="range"
        min={10}
        max={120}
        value={task.duration_seconds}
        onChange={(e) => setNested("task", { duration_seconds: Number(e.target.value) })}
        className="w-full"
      />
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">{task.duration_seconds}s</span>
        <div className="flex gap-2">
          <button
            className="badge"
            onClick={() => setNested("task", { description: "stand still for the full duration" })}
            type="button"
          >
            Stand
          </button>
          <button
            className="badge"
            onClick={() => setNested("task", { description: "walk forward slowly" })}
            type="button"
          >
            Walk
          </button>
        </div>
      </div>
    </div>
  );
}

import { useSimStore } from "../../store/simStore";

export default function ScenePanel() {
  const scene = useSimStore((s) => s.config.scene);
  const setNested = useSimStore((s) => s.setNested);

  return (
    <div className="panel space-y-3">
      <h2 className="panel-title">Scene</h2>
      <select
        className="input"
        value={scene.environment}
        onChange={(e) => setNested("scene", { environment: e.target.value })}
      >
        <option value="empty">Empty</option>
        <option value="warehouse">Warehouse</option>
        <option value="outdoor_terrain">Outdoor Terrain</option>
      </select>
      <select
        className="input"
        value={scene.lighting}
        onChange={(e) => setNested("scene", { lighting: e.target.value })}
      >
        <option value="day">Day</option>
        <option value="artificial">Artificial</option>
        <option value="night">Night</option>
      </select>
      <label className="flex items-center gap-2 text-sm text-slate-300">
        <input
          type="checkbox"
          checked={scene.obstacles}
          onChange={(e) => setNested("scene", { obstacles: e.target.checked })}
        />
        Add Obstacles
      </label>
    </div>
  );
}

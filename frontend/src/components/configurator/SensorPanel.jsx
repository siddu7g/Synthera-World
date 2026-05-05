import { useSimStore } from "../../store/simStore";

export default function SensorPanel() {
  const sensors = useSimStore((s) => s.config.sensors);
  const setNested = useSimStore((s) => s.setNested);

  const item = (key) => (
    <label className="flex items-center justify-between rounded-lg border border-slate-800 p-2 text-sm" key={key}>
      <span>{key.toUpperCase()}</span>
      <input
        type="checkbox"
        checked={sensors[key]}
        onChange={(e) => setNested("sensors", { [key]: e.target.checked })}
      />
    </label>
  );

  return (
    <div className="panel space-y-2">
      <h2 className="panel-title">Sensors</h2>
      {["camera", "imu", "lidar"].map(item)}
    </div>
  );
}

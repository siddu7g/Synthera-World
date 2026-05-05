import { useEffect } from "react";
import { useSimStore } from "../../store/simStore";
import { useAssets } from "../../hooks/useAssets";

export default function RobotPanel() {
  const { loadAssets } = useAssets();
  const config = useSimStore((s) => s.config);
  const assets = useSimStore((s) => s.assets);
  const setNested = useSimStore((s) => s.setNested);

  useEffect(() => {
    loadAssets().catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const categoryAssets = assets[config.robot.category] || [];
    if (!categoryAssets.length) return;
    const hasCurrent = categoryAssets.some((x) => x.asset_path === config.robot.asset_path);
    if (!hasCurrent) {
      const first = categoryAssets[0];
      setNested("robot", { asset_path: first.asset_path, asset_name: first.name });
    }
  }, [assets, config.robot.category, config.robot.asset_path, setNested]);

  const list = assets[config.robot.category] || [];

  return (
    <div className="panel space-y-3">
      <h2 className="panel-title">Robot</h2>
      <select
        className="input"
        value={config.robot.category}
        onChange={(e) => setNested("robot", { category: e.target.value })}
      >
        <option value="humanoid">Humanoid</option>
        <option value="amr">AMR</option>
      </select>
      <select
        className="input"
        value={config.robot.asset_path}
        onChange={(e) => {
          const item = list.find((x) => x.asset_path === e.target.value);
          if (item) setNested("robot", { asset_path: item.asset_path, asset_name: item.name });
        }}
      >
        {list.map((item) => (
          <option key={item.asset_path} value={item.asset_path}>
            {item.name}
          </option>
        ))}
      </select>
      <div className="text-xs text-slate-400">{config.robot.asset_path}</div>
    </div>
  );
}

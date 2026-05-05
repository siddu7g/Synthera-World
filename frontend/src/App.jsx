import TopBar from "./components/layout/TopBar";
import RobotPanel from "./components/configurator/RobotPanel";
import ScenePanel from "./components/configurator/ScenePanel";
import SensorPanel from "./components/configurator/SensorPanel";
import ScriptViewer from "./components/viewer/ScriptViewer";
import LogPanel from "./components/output/LogPanel";
import HistoryPanel from "./components/output/HistoryPanel";
import PromptWorkspace from "./components/workspace/PromptWorkspace";

export default function App() {
  return (
    <div className="min-h-screen p-4 text-slate-100">
      <div className="mx-auto grid max-w-7xl gap-4">
        <TopBar />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="grid gap-4">
            <RobotPanel />
            <ScenePanel />
            <SensorPanel />
            <PromptWorkspace />
          </div>
          <div className="grid gap-4 lg:col-span-2">
            <ScriptViewer />
            <div className="grid gap-4 lg:grid-cols-2">
              <LogPanel />
              <HistoryPanel />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

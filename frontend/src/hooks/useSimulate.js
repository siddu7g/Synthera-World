import { useSimStore } from "../store/simStore";

export function useSimulate() {
  const backendUrl = useSimStore((s) => s.backendUrl);
  const generationId = useSimStore((s) => s.generationId);
  const addLog = useSimStore((s) => s.addLog);
  const clearLogs = useSimStore((s) => s.clearLogs);
  const setSimulating = useSimStore((s) => s.setSimulating);
  const setApiError = useSimStore((s) => s.setApiError);
  const setApiNotice = useSimStore((s) => s.setApiNotice);

  async function run() {
    if (!generationId) throw new Error("Generate a script first");
    clearLogs();
    setSimulating(true);
    setApiError("");
    setApiNotice("Simulation running...");
    try {
      const response = await fetch(`${backendUrl}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ generation_id: generationId })
      });
      if (!response.ok || !response.body) {
        throw new Error("Failed to start simulation");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        chunk
          .split("\n")
          .filter((line) => line.startsWith("data: "))
          .forEach((line) => addLog(line.replace("data: ", "")));
      }
      setApiNotice("Simulation finished");
    } catch (error) {
      setApiError(error.message || "Simulation failed");
      setApiNotice("Simulation failed");
      throw error;
    } finally {
      setSimulating(false);
    }
  }

  async function stop() {
    await fetch(`${backendUrl}/simulate/stop`, { method: "POST" });
    setApiNotice("Stop requested");
  }

  return { run, stop };
}

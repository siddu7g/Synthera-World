import { useSimStore } from "../store/simStore";

export function useGenerate() {
  const backendUrl = useSimStore((s) => s.backendUrl);
  const config = useSimStore((s) => s.config);
  const setGenerated = useSimStore((s) => s.setGenerated);
  const setGenerating = useSimStore((s) => s.setGenerating);
  const setApiError = useSimStore((s) => s.setApiError);
  const setApiNotice = useSimStore((s) => s.setApiNotice);

  async function generate() {
    setGenerating(true);
    setApiError("");
    setApiNotice("Generating script...");
    try {
      const response = await fetch(`${backendUrl}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      });
      const data = await response.json();
      if (!response.ok) {
        const message = typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail || data);
        throw new Error(message);
      }
      setGenerated(data.script, data.generation_id);
      setApiNotice(`Generated successfully (${data.model})`);
      return data;
    } catch (error) {
      setApiError(error.message || "Generation failed");
      setApiNotice("Generation failed");
      throw error;
    } finally {
      setGenerating(false);
    }
  }

  return { generate };
}

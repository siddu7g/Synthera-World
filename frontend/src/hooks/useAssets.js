import { useSimStore } from "../store/simStore";

export function useAssets() {
  const backendUrl = useSimStore((s) => s.backendUrl);
  const setAssets = useSimStore((s) => s.setAssets);
  const setApiError = useSimStore((s) => s.setApiError);

  async function loadAssets() {
    const response = await fetch(`${backendUrl}/assets`);
    if (!response.ok) {
      setApiError("Failed to load assets");
      throw new Error("Failed to load assets");
    }
    const data = await response.json();
    setAssets(data);
  }

  return { loadAssets };
}

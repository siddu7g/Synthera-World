# Synthera RAG Documents

Put project/domain context files here for retrieval-augmented chat in the UI.

## Supported files
- `.md`
- `.txt`

## Bundled baseline
- `humanoid_example.md` — RAG baseline from NVIDIA `humanoid_example.py` (two H1 walkers + policy pattern), plus **Nemotron anti-patterns**, **opposite-direction seven-second walk recipe**, and a **standalone skeleton** (`SimulationApp` ordering). Used by `/chat` and, when `RAG_FOR_GENERATE=true`, appended to `/generate` user prompts for humanoid-heavy retrieval. Restart backend after edits.

## Recommended docs to add
- `isaac_api_notes.md` - known working Isaac Sim 5.1 APIs you validated
- `robot_capabilities.md` - per-robot constraints and supported demo behaviors
- `asset_paths.md` - canonical asset and environment paths in your machine
- `troubleshooting.md` - known runtime errors + fixes
- `project_decisions.md` - architecture decisions and why
- `demo_playbook.md` - demo scripts and expected outputs

## Tips
- Keep sections short and concrete (retriever chunks by paragraphs).
- Prefer explicit examples over generic descriptions.
- Update docs as you debug issues, so chat improves automatically.

## Runtime config
Set in `.env`:

`RAG_DOCS_DIR=/home/sidg/isaacsim/Synthera World/rag`

If not set, backend defaults to `../rag` from `backend/`.

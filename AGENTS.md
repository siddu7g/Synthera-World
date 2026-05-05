# AGENTS.md — Synthera World (Beta v0)

> **Read this entire file before writing any code.**
> This is the single source of truth for Synthera World. Every architectural decision,
> naming convention, API choice, and build order is defined here. Follow it exactly.

---

## Project Identity

**Name:** Synthera World
**Version:** Beta v0 (zero-to-running prototype)
**Tagline:** "Configure. Generate. Simulate."
**Mission:** A desktop application that lets users visually configure humanoid robot and AMR
simulation environments using NVIDIA Isaac Sim assets already installed on their computer,
then auto-generates and runs the Isaac Sim Python scripts via AI.

---

## Scope for Beta v0

Beta v0 is deliberately narrow. Build only what is listed here.

**In scope:**
- Interactive frontend to configure a simulation (robot type, scene, task, sensors)
- Load and display available humanoid + AMR assets from the user's local Isaac Sim installation
- AI-generated Isaac Sim Python script from the user's configuration
- Run the generated script against local Isaac Sim and stream logs back
- Save simulation records locally (SQLite)
- Basic script validation before execution

**Out of scope for beta v0:**
- Quadruped robots — Phase 1
- Drone robots — Phase 1
- RAG over Isaac Sim docs — Phase 1
- Synthetic data pipeline (omni.replicator) — Phase 1
- Multi-robot coordination — Phase 1
- ROS2 bridge — Phase 1
- Cloud deployment or multi-user — Phase 2
- Fine-tuned model — Phase 2

---

## Robot Focus

Beta v0 supports exactly two robot categories:

### Humanoids
Primary asset: **Unitree H1**
- USD path: `/Isaac/Robots/Unitree/H1/h1.usd`
- Type: biped humanoid
- Controller: full-body articulation via joint position targets
- Supported tasks in beta: stand, walk forward, walk to waypoint, wave arm

### AMRs (Autonomous Mobile Robots)
Primary assets:
- **Clearpath Ridgeback** — `/Isaac/Robots/Clearpath/Ridgeback/ridgeback.usd`
- **Clearpath Jackal** — `/Isaac/Robots/Clearpath/Jackal/jackal.usd`
- **NVIDIA Carter v1** — `/Isaac/Robots/Carter/carter_v1.usd`
- Controller: DifferentialController (wheel velocity commands)
- Supported tasks in beta: drive to point, patrol waypoints, avoid obstacles

---

## AI Model

**Primary:** Claude via OpenRouter
- Dev/beta: `anthropic/claude-haiku-4-5-20251001` — fast, cheap, good for beta
- Production: `anthropic/claude-sonnet-4-6` — higher quality code generation
- Fallback/test: `nvidia/llama-3.1-nemotron-70b-instruct` via OpenRouter

Switch between models via `AI_MODEL` environment variable — no code changes needed.
Test Nemotron in parallel during beta to compare Isaac Sim code generation quality.

**Cost target for beta:** Under $5 total OpenRouter spend. Use Haiku throughout beta.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop shell | Electron 28+ |
| Frontend UI | React 18 + Vite + TailwindCSS |
| State management | Zustand |
| Backend server | FastAPI (Python 3.10) |
| AI client | OpenRouter REST API via httpx |
| Database | SQLite via SQLModel |
| Script editor | Monaco Editor (read-only default) |
| IPC | HTTP REST (Electron ↔ FastAPI on localhost:8765) |
| Simulation runtime | NVIDIA Isaac Sim 4.5 (local, user-installed) |
| Containerization | Docker (backend only) + native Isaac Sim on host |
| Package managers | npm (frontend/electron) + pip (backend) |

---

## Repository Structure

```
synthera-world/
├── AGENTS.md
├── .env                               ← secrets, never commit
├── .env.example                       ← safe template, commit this
├── .gitignore
├── docker-compose.yml
│
├── electron/
│   ├── main.js                        ← entry, spawns FastAPI, manages window
│   ├── preload.js                     ← secure IPC bridge
│   └── package.json
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── store/
│       │   └── simStore.js            ← Zustand: sim config + run state
│       ├── hooks/
│       │   ├── useGenerate.js
│       │   ├── useSimulate.js         ← SSE handler
│       │   └── useAssets.js
│       └── components/
│           ├── layout/
│           │   ├── Sidebar.jsx
│           │   └── TopBar.jsx
│           ├── configurator/
│           │   ├── RobotPanel.jsx     ← humanoid vs AMR + asset picker
│           │   ├── ScenePanel.jsx     ← environment + lighting + obstacles
│           │   ├── TaskPanel.jsx      ← natural language task + duration
│           │   └── SensorPanel.jsx    ← camera/IMU/LiDAR toggles
│           ├── viewer/
│           │   ├── ScriptViewer.jsx   ← Monaco editor, generated Python
│           │   └── AssetPreview.jsx   ← thumbnail/info for selected robot
│           ├── controls/
│           │   └── SimControls.jsx    ← Generate / Run / Stop buttons
│           └── output/
│               ├── LogPanel.jsx       ← live SSE log stream
│               └── HistoryPanel.jsx   ← past runs from SQLite
│
├── backend/
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── routers/
│   │   ├── generate.py                ← POST /generate
│   │   ├── simulate.py                ← POST /simulate, POST /simulate/stop
│   │   ├── assets.py                  ← GET /assets
│   │   └── history.py                 ← GET /simulations
│   ├── services/
│   │   ├── ai_client.py               ← OpenRouter wrapper, model switching
│   │   ├── prompt_builder.py          ← system + user prompt assembly
│   │   ├── script_validator.py        ← AST linter + API surface checker
│   │   ├── isaac_runner.py            ← subprocess manager
│   │   └── asset_scanner.py           ← scans local Isaac Sim USDs
│   ├── models/
│   │   ├── sim_config.py              ← Pydantic SimConfig schema
│   │   ├── responses.py               ← GenerateResponse, SimulationRecord
│   │   └── database.py                ← SQLModel tables + DB init
│   └── data/
│       ├── asset_catalog.json         ← generated by asset_scanner.py
│       ├── api_reference.json         ← allowed Isaac Sim API surface
│       └── robot_plugins/
│           ├── humanoid.json
│           └── amr.json
│
├── scripts/
│   ├── setup.sh
│   ├── scan_assets.py
│   └── validate_install.py
│
└── isaac_templates/
    ├── base_sim.py
    ├── humanoid_stand.py
    └── amr_waypoint.py
```

---

## Beta v0 Build Order

Build in this exact sequence. Do not skip steps.

### Step 0 — Environment validation (Day 1)
1. Run `scripts/validate_install.py` — confirms Isaac Sim 4.5, Python 3.10, CUDA present
2. Run `scripts/scan_assets.py` — generates `asset_catalog.json` from local install
3. Manually run `isaac_templates/humanoid_stand.py` in Isaac Sim Python — confirm H1 loads
4. Manually run `isaac_templates/amr_waypoint.py` — confirm AMR assets load
5. **Done when:** Both templates run without errors

### Step 1 — Backend core (Day 1–2)
1. FastAPI skeleton with `/health` endpoint
2. `models/sim_config.py` — full Pydantic schema
3. `models/database.py` — SQLite at `~/.synthera-world/synthera.db`
4. `services/ai_client.py` — OpenRouter call, model switching via env var
5. `services/prompt_builder.py` — system prompt + user message assembly
6. `POST /generate` — SimConfig in, Python script out
7. **Done when:** curl returns valid Python for both humanoid and AMR configs

### Step 2 — Script validation (Day 2)
1. `services/script_validator.py` — 5 layers (see validation section)
2. Wire into `/generate` — never return unvalidated script
3. **Done when:** Fake API calls return line-level errors

### Step 3 — Isaac Sim runner (Day 2–3)
1. `services/isaac_runner.py` — subprocess via `ISAAC_SIM_PATH` env var
2. asyncio subprocess + stdout streaming
3. 5-minute safety timeout
4. `POST /simulate` with SSE
5. **Done when:** AMR script runs headlessly, logs stream back

### Step 4 — Asset scanner (Day 3)
1. `services/asset_scanner.py` — walks Isaac Sim install, finds humanoid + AMR USDs
2. Writes `asset_catalog.json`
3. `GET /assets` endpoint
4. **Done when:** Frontend receives list of locally available robot USDs

### Step 5 — Electron + React frontend (Day 3–5)
1. Electron shell — spawns FastAPI, opens localhost:3000
2. RobotPanel — Humanoid / AMR toggle + asset picker from `/assets`
3. ScenePanel — environment, lighting, obstacles
4. TaskPanel — textarea + duration slider + quick-pick chips
5. SensorPanel — checkboxes
6. SimControls — Generate → Run flow
7. ScriptViewer — Monaco editor with generated Python
8. LogPanel — SSE consumer
9. HistoryPanel — past runs from SQLite
10. **Done when:** Full flow works end-to-end through UI

---

## SimConfig Schema

```typescript
interface SimConfig {
  robot: {
    category: "humanoid" | "amr";
    asset_name: string;           // must match asset_catalog.json
    asset_path: string;           // validated nucleus USD path
  };
  scene: {
    environment: "warehouse" | "empty" | "outdoor_terrain";
    lighting: "day" | "artificial" | "night";
    obstacles: boolean;
  };
  task: {
    description: string;          // natural language, max 500 chars
    duration_seconds: number;     // 10–120 for beta
  };
  sensors: {
    camera: boolean;
    imu: boolean;
    lidar: boolean;
  };
  output: {
    headless: boolean;            // default true
    export_telemetry: boolean;
  };
}
```

---

## AI Prompt Architecture

### System Prompt (cached at startup — never rebuilt per request)

```
You are an expert NVIDIA Isaac Sim 4.5 Python script generator for Synthera World.
You write clean, correct, immediately runnable Isaac Sim Python scripts.

STRICT RULES:
1. Only use APIs from ALLOWED API SURFACE below. Never invent methods.
2. SimulationApp must be instantiated BEFORE any other isaacsim import.
3. All asset paths must come exactly from ASSET CATALOG below.
4. Never use deprecated omni.isaac.* namespace. Use isaacsim.* only.
5. Always call simulation_app.close() in a finally block.
6. Never use time.sleep() — use world.step() for timing.
7. Return only the Python script. No markdown, no explanation, no preamble.

ROBOT FOCUS: Humanoids (Unitree H1) and AMRs only.
Humanoids: use articulation API with joint position targets.
AMRs: use WheeledRobot + DifferentialController pattern.

SCRIPT STRUCTURE:
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": HEADLESS_BOOL})

import numpy as np
from isaacsim.core.api import World
# additional imports after SimulationApp

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

# ASSET LOADING
# ROBOT SETUP
# SENSOR SETUP
# SIMULATION LOOP
world.reset()
try:
    for i in range(DURATION_STEPS):
        world.step(render=RENDER_BOOL)
except KeyboardInterrupt:
    pass
finally:
    simulation_app.close()

ALLOWED API SURFACE:
{api_reference}

ASSET CATALOG:
{asset_catalog}
```

### User Message (per request — not cached)

```
Generate an Isaac Sim Python script:

Robot: {robot.category} — {robot.asset_name}
Asset path: {robot.asset_path}
Environment: {scene.environment}, lighting: {scene.lighting}, obstacles: {scene.obstacles}
Task: {task.description}
Duration: {duration_steps} steps ({task.duration_seconds}s at 60Hz)
Sensors: camera={sensors.camera}, imu={sensors.imu}, lidar={sensors.lidar}
Headless: {output.headless}
```

---

## Script Validation (5 Layers)

```python
# Layer 1: Syntax
ast.parse(script)

# Layer 2: Forbidden patterns
FORBIDDEN = ["omni.isaac.", "subprocess", "os.system", "eval(", "exec(", "__import__"]

# Layer 3: API surface — AST walk, check isaacsim.* calls vs api_reference.json

# Layer 4: Asset paths — extract /Isaac/ strings, check vs asset_catalog.json

# Layer 5: Import order — SimulationApp must appear before all other isaacsim imports
```

---

## Database

**Engine:** SQLite via SQLModel
**File:** `~/.synthera-world/synthera.db`
**Type:** Relational database (tables/rows/SQL — same family as PostgreSQL, NOT a vector DB)

```python
class SimulationRecord(SQLModel, table=True):
    generation_id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    robot_category: str              # "humanoid" or "amr"
    robot_name: str
    task_description: str
    config_json: str                 # full SimConfig as JSON string
    script_path: str                 # path to generated .py file
    status: str = "pending"          # pending/running/complete/failed
    duration_s: Optional[float] = None
    exit_code: Optional[int] = None
    telemetry_path: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    ai_model: str = "anthropic/claude-haiku-4-5-20251001"
```

**Local folder structure:**
```
~/.synthera-world/
├── synthera.db
└── simulations/
    └── <generation_id>/
        ├── script.py
        ├── config.json
        └── telemetry.json
```

---

## Containerization

**2 containers + Isaac Sim native:**

```yaml
# docker-compose.yml
version: "3.9"
services:
  synthera-backend:
    build: ./backend
    container_name: synthera-backend
    ports:
      - "8765:8765"
    volumes:
      - ${HOME}/.synthera-world:/root/.synthera-world
      - ${ISAAC_SIM_PATH}:/isaac-sim:ro
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - AI_MODEL=${AI_MODEL:-anthropic/claude-haiku-4-5-20251001}
      - ISAAC_SIM_PYTHON=/isaac-sim/python.sh
      - SYNTHERA_DATA_DIR=/root/.synthera-world
    restart: unless-stopped

  synthera-frontend:
    build: ./frontend
    container_name: synthera-frontend
    ports:
      - "3000:3000"
    depends_on: [synthera-backend]
    profiles: [browser-ui]          # optional, Electron doesn't need this
```

**Isaac Sim runs natively — never in Docker.**
Reasons: direct RTX GPU required, host CUDA driver dependency,
NVIDIA EULA personal acceptance, ~25GB size.

---

## Environment Variables

```bash
# .env (never commit)
OPENROUTER_API_KEY=sk-or-v1-...
AI_MODEL=anthropic/claude-haiku-4-5-20251001
# options: anthropic/claude-haiku-4-5-20251001
#          anthropic/claude-sonnet-4-6
#          nvidia/llama-3.1-nemotron-70b-instruct
ISAAC_SIM_PATH=/home/<user>/.local/share/ov/pkg/isaacsim-4.5.0
SYNTHERA_DATA_DIR=~/.synthera-world
SIMGEN_ENV=dev
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/generate` | SimConfig → AI → validated Isaac Sim script |
| `POST` | `/simulate` | Run script → Isaac Sim → SSE log stream |
| `POST` | `/simulate/stop` | Kill running Isaac Sim subprocess |
| `GET` | `/simulations` | Fetch history from SQLite |
| `GET` | `/assets` | Return locally available humanoid + AMR assets |
| `GET` | `/health` | FastAPI alive, Isaac Sim reachable, API key valid |

---

## Request → AI → Response Flow

```
1.  Frontend sends SimConfig → POST /generate
2.  Pydantic validates schema
3.  prompt_builder assembles system prompt (cached) + user message
4.  ai_client calls OpenRouter (model from AI_MODEL env var)
    temperature=0.1, max_tokens=2048, awaited async ~3–8s
5.  script_validator runs 5 layers
6.  Script written → ~/.synthera-world/simulations/<uuid>/script.py
7.  SimulationRecord inserted → synthera.db (status=pending)
8.  GenerateResponse returned to frontend
9.  User clicks Run → POST /simulate
10. isaac_runner spawns Isaac Sim Python subprocess
11. SSE stream: stdout → LogPanel live
12. On exit: update record status, duration, exit_code in SQLite
```

---

## Async, Caching, Rate Limiting

**Async:** Full async/await. Claude call via `httpx.AsyncClient`. Isaac Sim subprocess via
`asyncio.create_subprocess_exec`. All SSE streaming non-blocking.

**Caching:**
- System prompt loaded once at startup into `app.state` — zero disk reads per request
- OpenRouter `cache_control` on system prompt — ~90% input token cost reduction after first call

**Rate limiting:**
- 5-second cooldown between `/generate` calls (in-memory timestamp, no Redis needed)
- Single simulation lock — `/simulate` returns HTTP 409 if Isaac Sim already running
- Cost tracking: `tokens_used` + `cost_usd` logged to SQLite every generation

---

## Coding Conventions

- Python: PEP 8, type hints everywhere, docstring on all public methods
- React: functional components only, Zustand for shared state, no prop drilling
- All FastAPI routes async — no blocking calls
- Logging: Python `logging` module, not print statements
- No hardcoded paths — everything from env vars or `app.state`
- No secrets in source — API key from `.env` only
- Generated scripts never auto-deleted — user controls cleanup

---

## Development Setup

```bash
# 1. Clone
git clone https://github.com/yourname/synthera-world && cd synthera-world

# 2. Validate Isaac Sim
python scripts/validate_install.py

# 3. Scan local assets
python scripts/scan_assets.py

# 4. Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # then add your keys

# 5. Test with curl (no UI needed yet)
uvicorn main:app --reload --port 8765
curl -X POST http://localhost:8765/generate \
  -H "Content-Type: application/json" \
  -d '{"robot":{"category":"amr","asset_name":"Clearpath Jackal",
       "asset_path":"/Isaac/Robots/Clearpath/Jackal/jackal.usd"},
       "scene":{"environment":"warehouse","lighting":"day","obstacles":false},
       "task":{"description":"drive in a square pattern","duration_seconds":30},
       "sensors":{"camera":false,"imu":true,"lidar":false},
       "output":{"headless":true,"export_telemetry":false}}'

# 6. Frontend
cd ../frontend && npm install && npm run dev

# 7. Electron
cd ../electron && npm install && npm start

# Dev without Isaac Sim running:
# Set ISAAC_SIM_PYTHON=echo — runner prints script path instead of executing
```

---

## Critical Isaac Sim Note

> All `isaacsim.*` imports MUST come after `SimulationApp` is instantiated.
> The Omniverse extension system must boot first.
> Importing before SimulationApp will crash immediately.
> The script validator enforces this as Layer 5 on every generated script.

---

*Synthera World — Beta v0 | 2026-03-26*
*Focus: Humanoids (Unitree H1, Other Robots) + AMRs (Ridgeback, Jackal, Carter)*
*AI: Claude Haiku (dev) / Claude Sonnet or Nemotron 70B (prod) via OpenRouter*

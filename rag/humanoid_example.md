# Humanoid baseline (NVIDIA `humanoid_example.py`)

This document is the Synthera RAG baseline for **Unitree H1** interactive walking. It mirrors the official sample: two `H1FlatTerrainPolicy` instances, flat ground, physics-step velocity commands, different stop timers (governed vs ungoverned).

**Synthera humanoid generation contract:** Generated `humanoid_example.py` must be an **interactive BaseSample extension** (not a standalone SimulationApp script).

Keywords for retrieval: humanoid H1 Unitree walk forward velocity policy physics step ground plane prim path World governance two robots.

## Critical guardrails (read first)

These are high-priority constraints for Claude Opus/Nemotron retrieval. If any conflict appears elsewhere, follow this section.

- **SCRIPT MODE (MANDATORY): ALWAYS BaseSample extension, NEVER standalone SimulationApp.**
- **Generated file must be:** class `HumanoidExample(BaseSample)`.
- **Required methods:** `__init__`, `setup_scene`, `setup_post_load`, `setup_post_reset`, `on_physics_step`, `_timeline_timer_callback_fn`, `world_cleanup`.
- **NEVER emit:** `from isaacsim import SimulationApp`, `simulation_app.close()`, any standalone `try/finally` runtime wrapper, or top-level `for` loop calling `world.step()`.
- **Correct top-level imports, always in this order:**
  - `import carb`
  - `import numpy as np`
  - `import omni`
  - `import omni.appwindow`
  - `from isaacsim.examples.interactive.base_sample import BaseSample`
  - `from isaacsim.robot.policy.examples.robots.h1 import H1FlatTerrainPolicy`
  - `from isaacsim.storage.native import get_assets_root_path`
- **NEVER (hallucinated module):** `from isaacsim.robot.wheeled_robots import ...` in H1 humanoid scripts.
- **ALWAYS (humanoid policy import):** `from isaacsim.robot.policy.examples.robots.h1 import H1FlatTerrainPolicy`
- **NEVER hardcode** `/Isaac/...` with fake roots like `assets_root_path = "/Isaac"`.
- **ALWAYS resolve USD via assets root:** `usd_path = get_assets_root_path() + "/Isaac/Robots/Unitree/H1/h1.usd"`
- **ALWAYS match NVIDIA timing for accumulated seconds:** `physics_dt = 1.0 / 200.0` (not `1/60`) unless the world is explicitly configured otherwise.
- **For 7-second behavior:** use `t += physics_dt`; stop when `t >= 7.0`.

Negative example block for retrieval:

```python
# NEVER:
from isaacsim import SimulationApp
from isaacsim.robot.wheeled_robots import DifferentialController
assets_root_path = "/Isaac"
physics_dt = 1.0 / 60.0
simulation_app = SimulationApp({"headless": True})
try:
    for _ in range(1200):
        world.step(render=False)
finally:
    simulation_app.close()
```

Correct example block for retrieval:

```python
import carb
import numpy as np
import omni
import omni.appwindow
from isaacsim.examples.interactive.base_sample import BaseSample
from isaacsim.robot.policy.examples.robots.h1 import H1FlatTerrainPolicy
from isaacsim.storage.native import get_assets_root_path
physics_dt = 1.0 / 200.0
usd_path = get_assets_root_path() + "/Isaac/Robots/Unitree/H1/h1.usd"
class HumanoidExample(BaseSample):
    ...
```

## Nemotron-style mistakes to never emit (standalone scripts)

Models often mash the interactive sample with a guessed loop. **Do not** produce broken output like these patterns. Keywords: nemotron mistake wrong import order missing SimulationApp undefined World hallucination backward forward opposite timer.

Always include, in order: `from isaacsim import SimulationApp`, then `simulation_app = SimulationApp({"headless": HEADLESS_BOOL})`, then remaining imports including `from isaacsim.core.api import World`. Never call `simulation_app.close()` without defining `simulation_app` the same way.

Never use `World(...)` without importing `World` from `isaacsim.core.api`.

Do **not** paste the interactive sample’s import block (`BaseSample`, leading `carb` / `omni` / `omni.appwindow`) as the **top** of a standalone file if that pushes any `isaacsim` import above `SimulationApp` init. For standalone, you can omit `BaseSample` entirely and drive policies from the main loop after `world.step`.

Never hardcode `assets_root_path = "/Isaac"` or a shortened USD root. Use `get_assets_root_path()` and concatenate exactly `"/Isaac/Robots/Unitree/H1/h1.usd"` so paths resolve on real installs.

Do **not** call `initialize()`, `post_reset()`, and `set_joints_default_state(...)` on every timestep. The NVIDIA reference runs that block **once** when transitioning from `_physics_ready == False` to True (first physics phase). After that, only `forward(step_size, cmd)` runs each step.

Accumulate elapsed time with the **same dt** the physics/policy sees. For this NVIDIA H1 baseline, use `1/200` (not `1/60`) so the 7-second window aligns with expected simulated time.

Avoid redundant condition branches (for example walking backward duplicated in nested `if` / `elif` for the same robot); use one clear rule per robot per phase.

## Two H1 opposite directions same corridor seven seconds then stop

Use prim `/World/H1` and `/World/H1_01`. Keep NVIDIA-style spawn offsets so both walk parallel along the **same forward axis** but slightly separated sideways (example positions `[-2.0, 2.0, 1.05]` and `[-2.0, 3.0, 1.05]`): opposite **velocity commands** mean opposite motion along forward, not crossing paths.

Define `walk_fwd = [0.75, 0.0, 0.0]`, `walk_back = [-0.75, 0.0, 0.0]`, `stop_cmd = [0.0, 0.0, 0.0]`. Let `t` accumulate simulation seconds. While `t < 7.0`: call `h1.forward(step_size, walk_fwd)` and `h2.forward(step_size, walk_back)`. When `t >= 7.0`: call both with `stop_cmd`. Increment `t += step_size` each physics step **after** applying commands (mirror NVIDIA ordering: increment timer while `_physics_ready` inside step logic).

For standalone loops using `world.step(render=...)`, obtain `step_size` consistently from the world’s physics timestep so seven seconds wall-clock in simulation matches seven accumulated seconds.

## Script mode note

Any prior standalone `SimulationApp` examples are deprecated for humanoid generation in this project context. Use the BaseSample lifecycle and callback style only.

## World timing settings

`stage_units_in_meters` 1.0, `physics_dt` 1/200, `rendering_dt` 8/200. Internal `_step_timer` and `_physics_ready` gate when walk commands apply.

## Walk and stop commands

Velocity command list format: forward, lateral, yaw. Walk uses approximately `[0.75, 0.0, 0.0]`. Stop uses `[0.0, 0.0, 0.0]`. Robot A (`H1_Governed`) walks while `_step_timer` under 4.0 seconds then stops. Robot B (`H1_Ungoverned`) walks while timer under 8.0 seconds then stops.

## Asset path and spawn offsets

Resolve USD with `get_assets_root_path()` plus `"/Isaac/Robots/Unitree/H1/h1.usd"`. Robot A: `prim_path="/World/H1"`, `name="H1_Governed"`, `position=np.array([-2.0, 2.0, 1.05])`. Robot B: `prim_path="/World/H1_01"`, `name="H1_Ungoverned"`, `position=np.array([-2.0, 3.0, 1.05])`.

## Ground plane

`add_default_ground_plane` with `z_position=0`, friction 0.2/0.2, `restitution=0.01`, `prim_path="/World/defaultGroundPlane"`, `name="default_ground_plane"`.

## Physics callback pattern

Register `physics_step` on the world. First phase: `_physics_ready` false — call `initialize()`, `post_reset()`, `robot.robot.set_joints_default_state(robot.default_pos)` for each robot. Then set `_physics_ready` true. Each step: increment timer by `step_size`, call `self.h1.forward(step_size, cmd)` and `self.h2.forward(step_size, cmd)` with walk or stop list depending on elapsed time.

## Timeline hook

Subscribe to `omni.timeline` PLAY events so `_physics_ready` resets when the timeline plays again (sample uses `_timeline_timer_callback_fn`).

## Imports (interactive sample — not the Synthera standalone shape)

```python
import carb
import numpy as np
import omni
import omni.appwindow
from isaacsim.examples.interactive.base_sample import BaseSample
from isaacsim.robot.policy.examples.robots.h1 import H1FlatTerrainPolicy
from isaacsim.storage.native import get_assets_root_path
```

## Class init and command state

```python
class HumanoidExample(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._world_settings["stage_units_in_meters"] = 1.0
        self._world_settings["physics_dt"] = 1.0 / 200.0
        self._world_settings["rendering_dt"] = 8.0 / 200.0
        self._step_timer = 0.0
        self._physics_ready = False
        self._walk_cmd = [0.75, 0.0, 0.0]
        self._stop_cmd = [0.0, 0.0, 0.0]
```

## setup_scene: plane and two H1 policies

```python
    def setup_scene(self) -> None:
        self.get_world().scene.add_default_ground_plane(
            z_position=0,
            name="default_ground_plane",
            prim_path="/World/defaultGroundPlane",
            static_friction=0.2,
            dynamic_friction=0.2,
            restitution=0.01,
        )
        assets_root_path = get_assets_root_path()
        usd_path = assets_root_path + "/Isaac/Robots/Unitree/H1/h1.usd"
        self.h1 = H1FlatTerrainPolicy(
            prim_path="/World/H1",
            name="H1_Governed",
            usd_path=usd_path,
            position=np.array([-2.0, 2.0, 1.05]),
        )
        self.h2 = H1FlatTerrainPolicy(
            prim_path="/World/H1_01",
            name="H1_Ungoverned",
            usd_path=usd_path,
            position=np.array([-2.0, 3.0, 1.05]),
        )
        timeline = omni.timeline.get_timeline_interface()
        self._event_timer_callback = timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
            int(omni.timeline.TimelineEventType.PLAY), self._timeline_timer_callback_fn
        )
```

## Async setup and physics step body

```python
    async def setup_post_load(self) -> None:
        if not self.get_world().physics_callback_exists("physics_step"):
            self.get_world().add_physics_callback("physics_step", callback_fn=self.on_physics_step)
        await self.get_world().play_async()

    async def setup_post_reset(self) -> None:
        self._step_timer = 0.0
        self._physics_ready = False
        if not self.get_world().physics_callback_exists("physics_step"):
            self.get_world().add_physics_callback("physics_step", callback_fn=self.on_physics_step)
        await self.get_world().play_async()

    def on_physics_step(self, step_size) -> None:
        if self._physics_ready:
            self._step_timer += step_size
            if self._step_timer < 4.0:
                self.h1.forward(step_size, self._walk_cmd)
            else:
                self.h1.forward(step_size, self._stop_cmd)
            if self._step_timer < 8.0:
                self.h2.forward(step_size, self._walk_cmd)
            else:
                self.h2.forward(step_size, self._stop_cmd)
        else:
            self._physics_ready = True
            for robot in [self.h1, self.h2]:
                robot.initialize()
                robot.post_reset()
                robot.robot.set_joints_default_state(robot.default_pos)
```

## Timeline callback and cleanup

```python
    def _timeline_timer_callback_fn(self, event) -> None:
        if self.h1 and self.h2:
            self._physics_ready = False

    def world_cleanup(self):
        world = self.get_world()
        self._event_timer_callback = None
        if world.physics_callback_exists("physics_step"):
            world.remove_physics_callback("physics_step")
```

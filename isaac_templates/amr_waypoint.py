from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

from isaacsim.core.api import World
from isaacsim.core.prims import XFormPrim


world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

XFormPrim(
    prim_path="/World/Jackal",
    name="jackal",
    usd_path="/Isaac/Robots/Clearpath/Jackal/jackal.usd",
)

world.reset()
try:
    for _ in range(600):
        world.step(render=False)
finally:
    simulation_app.close()

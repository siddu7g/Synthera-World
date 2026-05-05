from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

from isaacsim.core.api import World


world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

world.reset()
try:
    for _ in range(600):
        world.step(render=False)
finally:
    simulation_app.close()

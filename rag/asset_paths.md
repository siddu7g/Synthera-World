# Asset and Script Paths

## Isaac assets root
- `/home/sidg/isaacsim_assets/Assets/Isaac/5.1`

## Robots folder
- `/home/sidg/isaacsim_assets/Assets/Isaac/5.1/Isaac/Robots`

## Preferred Nemotron humanoid output script path
- `/home/sidg/isaacsim/exts/isaacsim.examples.interactive/isaacsim/examples/interactive/humanoid/nemotron_humanoid.py`

Behavior:
- For humanoid generations when the selected model contains `nemotron`, backend mirrors the generated script to the above path.
- The normal generation artifact is still saved in `SYNTHERA_DATA_DIR/simulations/<generation_id>/script.py`.

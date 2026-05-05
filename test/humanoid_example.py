# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import carb
import numpy as np
import omni
import omni.appwindow
from isaacsim.examples.interactive.base_sample import BaseSample
from isaacsim.robot.policy.examples.robots.h1 import H1FlatTerrainPolicy
from isaacsim.storage.native import get_assets_root_path

physics_dt = 1.0 / 200.0


class HumanoidExample(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_ready = False
        self._elapsed_time = 0.0
        self._event_timer_callback = None
        self.h1 = None
        self.h2 = None

    def setup_scene(self) -> None:
        world = self.get_world()
        world.scene.add_default_ground_plane(
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
            position=np.array([0.0, 0.5, 1.05]),
        )
        self.h2 = H1FlatTerrainPolicy(
            prim_path="/World/H1_01",
            name="H1_Ungoverned",
            usd_path=usd_path,
            position=np.array([0.0, -0.5, 1.05]),
        )
        timeline = omni.timeline.get_timeline_interface()
        self._event_timer_callback = timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
            int(omni.timeline.TimelineEventType.PLAY), self._timeline_timer_callback_fn
        )

    async def setup_post_load(self) -> None:
        world = self.get_world()
        world.set_simulation_dt(physics_dt=physics_dt, rendering_dt=physics_dt)
        self._physics_ready = False
        self._elapsed_time = 0.0
        world.add_physics_callback("physics_step", callback_fn=self.on_physics_step)

    async def setup_post_reset(self) -> None:
        self._physics_ready = False
        self._elapsed_time = 0.0

    def on_physics_step(self, step_size) -> None:
        if not self._physics_ready:
            self.h1.initialize()
            self.h1.post_reset()
            self.h1.robot.set_joints_default_state(self.h1.default_pos)
            self.h2.initialize()
            self.h2.post_reset()
            self.h2.robot.set_joints_default_state(self.h2.default_pos)
            self._physics_ready = True
            self._elapsed_time = 0.0
            return

        self._elapsed_time += step_size

        if self._elapsed_time < 7.0:
            cmd_h1 = np.array([0.75, 0.0, 0.0])
            cmd_h2 = np.array([-0.75, 0.0, 0.0])
        else:
            cmd_h1 = np.array([0.0, 0.0, 0.0])
            cmd_h2 = np.array([0.0, 0.0, 0.0])

        self.h1.forward(step_size, cmd_h1)
        self.h2.forward(step_size, cmd_h2)

    def _timeline_timer_callback_fn(self, event) -> None:
        self._physics_ready = False
        self._elapsed_time = 0.0

    def world_cleanup(self) -> None:
        world = self.get_world()
        if world.physics_callback_exists("physics_step"):
            world.remove_physics_callback("physics_step")
        self._event_timer_callback = None
        self.h1 = None
        self.h2 = None
        self._physics_ready = False
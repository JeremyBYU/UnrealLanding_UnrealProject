"""Spawn Asets in Unreal Map
"""

from __future__ import print_function, division    # (at top of module)
import random
import sys
import os

def update_paths():
    sys.path.insert(0, os.path.dirname(__file__))
    DLL_PATH = os.path.join(os.path.abspath(sys.prefix), "Library/bin")
    ORIGINAL_PATH = os.environ['PATH']
    os.environ['PATH'] = "%s;%s" % (DLL_PATH, ORIGINAL_PATH)

update_paths()

from unreal import  ScopedSlowTask
import numpy as np

import levelgenerator
from levelgenerator.helper import import_assets_config, import_world


def create_random_world(seed=1):
    random.seed(seed)
    np.random.seed(seed)
    assets = import_assets_config("assets.json")
    buildings = import_world("point_cloud_map.json")
    total_frames = len(assets['assets']) * len(buildings)
    with ScopedSlowTask(total_frames, "Adding roof assets...") as slow_task:
        slow_task.make_dialog(True)
        levelgenerator.place_assets_in_map(assets, buildings, slow_task=slow_task)

def main():
    seed = 7
    create_random_world(seed)


if __name__ == "__main__":
    main()
"""Spawns Assets given a configuration file
"""

from __future__ import print_function, division    # (at top of module)
from os import path
import re
import logging
import sys
import random
import math
from copy import deepcopy
from shapely.geometry import shape, Point, box
from shapely.algorithms.polylabel import polylabel

import unreal
from unreal import EditorAssetLibrary as ual, EditorLevelLibrary as ull, Vector, Rotator

from levelgenerator.helper import import_rooftop_data, update
from levelgenerator.sampling import QuantitySampler

# Setup logger
logger = logging.getLogger("LevelGenerator")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


BLUE = '#6699cc'
GRAY = '#999999'

DEFAULT_ASSET = {
    "quantity": {
        "mean": 1,
        "distribution": "constant"
    },
    "probability_placement": 0.50,
    "place_on": ["*"],
    "place_on_constraints": [],
    "rotation": {
        "yaw": 0,
        "range": 0
    },
    "position": {
        "offset": {
            "z": 0.0
        },
        "min_dist_from_border": 0.0,
        "distribution": "uniform"
    },
    "properties": {},
    "materials": []
}


def sample_point_uniform(reduced_geom, asset, feature, max_attempts=5):
    minx, miny, maxx, maxy = reduced_geom.bounds
    for i in range(max_attempts):
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if reduced_geom.contains(pnt):
            return (pnt.x, pnt.y)
    return None


def sample_point_normal(reduced_geom, pos, max_attempts=5):
    if pos['center'] == 'pia':
        pia = polylabel(reduced_geom)
        x_mean, y_mean = pia.x, pia.y
    elif pos['center'] == 'centroid':
        x_mean, y_mean = reduced_geom.centroid.x, reduced_geom.centroid.y
    else:
        x_mean, y_mean = reduced_geom.representative_point(
        ).x, reduced_geom.representative_point().y
    for i in range(max_attempts):
        pnt = Point(random.normalvariate(
            x_mean, pos['std']), random.normalvariate(y_mean, pos['std']))
        if reduced_geom.contains(pnt):
            return (pnt.x, pnt.y)
    return None


def generate_position(feature, asset, min_buffer_side):
    pos = asset['position']
    reduced_geom = feature['geometry'].buffer(
        -1 * (min_buffer_side + pos['min_dist_from_border']))
    # Check if the Geometry got to small!
    if reduced_geom.is_empty:
        return None
    # Sample Geometry distribution
    if pos['distribution'] == 'uniform':
        point = sample_point_uniform(reduced_geom, asset, feature)
    elif pos['distribution'] == 'normal':
        point = sample_point_normal(reduced_geom, pos)
    z_coord = feature['properties']['height'] + \
        asset['position']['offset']['z']
    if point is None:
        return None
    return {'x': point[0], 'y': point[1], 'z': z_coord}


def generate_rotation(asset):
    angle_names = ['roll', 'pitch', 'yaw']
    angle_names = list(filter(lambda angle_name: asset['rotation'].get(
        angle_name) is not None, angle_names))
    angles = {}
    for angle_name in angle_names:
        angle_mean = asset['rotation'].get(angle_name, 0)
        if isinstance(angle_mean, list):
            # User provided a list of angles, just perform a random choice
            angle = random.choice(angle_mean)
            angles[angle_name] = angle
        else:
            # User provided a single mean value. Sample from range
            angle_range = asset['rotation'].get('range', 0)
            low_angle = angle_mean - angle_range
            high_angle = angle_mean + angle_range
            angle = low_angle + (high_angle - low_angle) * random.random()
            angles[angle_name] = angle

    return angles


def create_bbox_geometry(actor_asset):
    origin, extent = actor_asset.get_actor_bounds(False)
    minx = origin.x - extent.x
    maxx = origin.x + extent.x
    miny = origin.y - extent.y
    maxy = origin.y + extent.y
    return box(minx, miny, maxx, maxy)


def cut_geometry(feature, asset, actor_asset):
    asset_geom = create_bbox_geometry(actor_asset)
    feature_geom = feature['geometry']
    cut_geom = feature_geom.difference(asset_geom)
    return cut_geom


def get_quantity_distribution(asset):
    # Determine quantity of the assets to place on the feature area
    if asset['quantity']['distribution'] == 'constant':
        quantity = asset['quantity']['mean']
    elif asset['quantity']['distribution'] == 'exponential':
        quantity = int(math.ceil(random.expovariate(
            1 / asset['quantity']['mean'])))
    else:
        quantity = 1

    return quantity


def spawn_actor(ue_object, x=0, y=0, z=0, roll=0, pitch=0, yaw=0, asset_uid="", label_prefix="generated_", folder_path="/generated"):
    location = Vector()
    location.x = x
    location.y = y
    location.z = z
    rotation = Rotator()
    rotation.roll = roll
    rotation.pitch = pitch
    rotation.yaw = yaw
    spawned_actor = ull.spawn_actor_from_object(ue_object, location, rotation)
    if spawned_actor is None:
        logger.error("Cant spawn actor %s with %r", asset_uid, ue_object)
        return None
    new_label = label_prefix + spawned_actor.get_actor_label() + "_" + asset_uid
    spawned_actor.set_actor_label(new_label)
    spawned_actor.set_folder_path(folder_path)
    return spawned_actor


def process_map_feature(feature, feature_label, asset, asset_obj, asset_lookup, quantity_sampler=None):
    """Creates asset(s) in the map feature provided """
    # ensure any constraints on map feature properties are met
    for constraint_property in asset['place_on_constraints']:
        if not feature['properties'].get(constraint_property):
            logger.debug("Feature %s does not meet all constraints for asset %s: %s",
                         feature_label, asset['uid'], constraint_property)
            return

    logger.debug("Feature %s meets all constraints for asset %s",
                 feature_label, asset['uid'])

    # Randomly generate a quantity
    if quantity_sampler and asset['quantity']['distribution'] == 'data':
        # Randomly generate a quantity for asset backed by data
        quantity = quantity_sampler.sample(asset['uid'])
        if quantity < 1:
            logger.debug("Feature %s did not obtain chance of placement for asset %s",
                         feature_label, asset['uid'])
            return
    else:
        # Randomly generate a quantity from a parameterized distribution
        # Determine probability of placement, return early if doesn't reach probability chance
        prob_placement = random.random()
        if prob_placement > asset['probability_placement']:
            logger.debug("Feature %s did not obtain chance of placement for asset %s: %.2f > %.2f",
                         feature_label, asset['uid'], prob_placement, asset['probability_placement'])
            return
        # Determine quantity of the assets to place on the feature area
        quantity = get_quantity_distribution(asset)

    logger.debug("Feature %s with %d %s being generated",
                 feature_label, quantity, asset['uid'])

    for i in range(quantity):
        min_buffer_side = max(asset['bounds'][1].x, asset['bounds'][1].y)
        position = generate_position(feature, asset, min_buffer_side)
        if position is None:
            logger.warning(
                "Could not find a position in feature %s to place asset %s", feature_label, asset['uid'])
            return
        rotation = generate_rotation(asset)
        position.update(rotation)
        position['asset_uid'] = asset['uid']
        actor_asset = spawn_actor(asset_obj, **position)
        # Ensure the feature geometry has the newly created asset's 2D footprint removed
        feature['geometry'] = cut_geometry(feature, asset, actor_asset)

        ## Change material if alternates provided
        if asset['materials']:
            # User provided a list of materials to select from
            material_str = random.choice(asset['materials'])
            material = get_material(asset, asset_lookup, material_str)
            if material and (actor_asset.get_class() == unreal.StaticMeshActor.static_class()):
                # Set Object Material only if material exists and the actor is a static mesh actor
                actor_asset.static_mesh_component.set_material(0, material)
            else:
                logger.error("Asset %s is not a static mesh actor to assign %s", actor_asset,  material_str)
        # Change random property values
        if asset['properties']:
            for property_name, values in asset['properties'].items():
                if not values:
                    continue
                value = random.choice(values)
                if property_name == 'Material':
                    # Special case (Blueprint Assets) if the property is a named Material
                    # transform material string into a material object
                    chosen_material = get_material(asset, asset_lookup, value)
                    actor_asset.set_editor_property("Material", chosen_material)
                else:
                    actor_asset.set_editor_property(property_name, value)

        logger.debug("Feature %s is spawning asset %s with the following qualities %r",
                     feature_label, asset['uid'], position)

        # fig, ax = plt.subplots(figsize=(8,8), nrows=1, ncols=1)
        # patch1 = PolygonPatch(feature['geometry'] , fc=BLUE, ec=BLUE, alpha=0.5, zorder=2)
        # ax.add_patch(patch1)
        # ax.axis('equal')
        # plt.show()


def process_map_features(features, feature_label, asset, asset_obj, asset_lookup, quantity_sampler=None):
    """For each map feature, possibly add asset"""
    # Loop through map features
    for feature in features:
        process_map_feature(feature, feature_label, asset, asset_obj, asset_lookup, quantity_sampler)


def get_material(asset, material_lookup, material):
    if not material_lookup.get(material):
        material_path  = path.join(asset['asset_material_path'], material)
        if not ual.does_asset_exist(material_path):
            logger.error("ERROR! Asset does not exist: %s", material_path)
            return None
        else:
            mat_obj = ual.load_asset(material_path)
            return mat_obj
    else:
        logger.debug("Asset already loaded: %s", material)
        return material_lookup[material]

# def load_materials(asset_lookup, assets):
#     get_material_strings(assets)

def place_assets_in_map(assets, ue_map, slow_task=None):
    """Randomly places assets in the unreal engine map specified by ue_map """
    asset_base_path = assets['asset_base_path']
    # Check if user specified to sample quantity data from csv file
    # Will place assets using a histogram
    if assets.get('assets_quantity_data'):
        quantity_sampler = QuantitySampler(
            import_rooftop_data(assets['assets_quantity_data']),
            assets.get('assets_quantity_fit', 'histogram'))
    else:
        quantity_sampler = None

    count = 0
    asset_lookup = {}
    # load_materials(asset_lookup, assets)
    # Copy over global properties of assets
    update(DEFAULT_ASSET, assets['default_asset_settings'])

    for asset_ in assets['assets']:
        if slow_task and slow_task.should_cancel():
            break
        # Give default asset options
        asset = deepcopy(DEFAULT_ASSET)
        update(asset, asset_)

        # Filters used to ensure that the asset is allowed to be placed on
        # a map feature
        regex_filters = [re.compile(filter_) for filter_ in asset['place_on']]
        # Loop through every map feature and add asset (probabilistically)
        for feature_label, features in ue_map.iteritems():
            if slow_task:
                if slow_task.should_cancel():
                    break
                slow_task.enter_progress_frame(1)
                count += 1
            # Choose random asset mesh, possibly overide properties
            # Must use deep copy...
            asset = deepcopy(DEFAULT_ASSET)
            update(asset, asset_)
            if isinstance(asset['asset_details'], list):
                # User passed in multiple static meshes to choose from
                asset_path = random.choice(asset['asset_details'])
                # print("Is list first", asset_path)
                if isinstance(asset_path, list):
                    # Use passed in overrides!
                    # First element should be path string, second element dictionary overrides
                    asset_details = asset_path[:]
                    asset_path = asset_details[0]
                    # print("Is list second", asset_path)
                    if len(asset_details) > 1 and isinstance(asset_details[1], dict):
                        asset = update(asset, asset_details[1])
            else:
                # User simply provided the asset path
                asset_path = asset['asset_details']

            # Get asset mesh src
            src = path.join(asset_base_path, asset_path)
            # Ensure assets exists and can be loaded
            if not ual.does_asset_exist(src):
                logger.error("ERROR! Asset does not exist: %s", src)
                continue
            else:
                logger.debug("Asset exists: %s", src)
            asset_obj = ual.load_asset(src)
            actor_asset = spawn_actor(asset_obj)
            if actor_asset is None:
                return
            asset['bounds'] = actor_asset.get_actor_bounds(False)
            actor_asset.destroy_actor()

            if not asset_obj:
                logger.error("ERROR! Asset could not be loaded: %s", src)
                continue
            logger.info("Processing Feature %s with asset %s", feature_label, asset['uid'])
  
            # Ensure that the asset is allowed to be placed on this map feature
            feature_allowed = False
            for regex_filter in regex_filters:
                if regex_filter.match(feature_label):
                    feature_allowed = True
                    break
            if not feature_allowed:
                continue
            # If we reached this point we know this asset can be placed on these features
            try:
                process_map_features(features, feature_label, asset, asset_obj, asset_lookup, quantity_sampler=quantity_sampler)
            except Exception as e:
                logger.exception("Error processing feature %s with asset %s", feature_label, asset['uid'])


def modify_building_rooftops():
    """ Modify building rooftop materials """
    pass

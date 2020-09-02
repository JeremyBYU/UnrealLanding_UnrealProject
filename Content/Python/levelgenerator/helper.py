import os
import json
from os import path
import collections
import sys
import logging


import pandas as pd
import numpy as np
from shapely.geometry import shape
import geojson
from unreal import EditorAssetLibrary as ual, EditorLevelLibrary as ull, Vector, Rotator

logger = logging.getLogger("LevelGenerator")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

DIR_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BASE_FOLDER = "/Game"

# Remove these rooftop items
REMOVE_LIST = ['pools', 'debris', 'solar-panel', 'human-occupation', 'empty']


def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def duplicate_level(level_name, suffix="_rooftops"):
    # run command on asset
    source = path.join(BASE_FOLDER, level_name)
    destination = path.join(BASE_FOLDER, level_name + suffix)

    ull.new_level_from_template(destination, source)

def get_top_roof(feature):
    return max(feature, key=lambda x: x['properties']['height'])

def import_assets_config(file_name):
    json_fname = path.join(DIR_PATH, file_name)
    with open(json_fname) as f:
        config = json.load(f)
    return config


def import_world(file_name):
    json_fname = path.join(DIR_PATH, file_name)
    feature_collection = None
    with open(json_fname) as f:
        feature_collection = geojson.load(f)

    buildings = {}
    for feature in feature_collection['features']:
        label = feature.properties['class_label']
        feature['geometry'] = shape(feature['geometry'])
        if buildings.get(label):
            buildings[label].append(feature)
        else:
            buildings[label] = [feature]

    # This code is specific to my use case. I want to know which one of the roof outlines are the highest
    # This is specific for multi-level roofs
    for key, feature in buildings.iteritems():
        if len(feature) > 1:
            top_roof = get_top_roof(feature)
            top_roof['properties']['highest_level'] = True
        else:
            feature[0]['properties']['highest_level'] = True

    return buildings


def import_rooftop_data(file_name, remove_list=REMOVE_LIST):
    """Convert rooftop object CSV file to DataFrame
    This is hyperspecific to our csv. In the end we are creating a DataFrame like this:
    Row - Observation of a single building
    Column - Rooftop Surface Feature. 
    Cell - Quantity of respective rooftop feature on observed building roof
    Arguments:
        file_name {str} -- File Name
    
    Keyword Arguments:
        remove_list {[type]} -- [description] (default: {REMOVE_LIST})
    
    Returns:
        [type] -- [description]
    """

    fpath = path.join(DIR_PATH, file_name)
    df_b = pd.read_csv(
        fpath,
        converters={'gps': lambda x: [float(coord) for coord in x.split(',')],
                    'quantity': lambda x: [int(quantity) for quantity in x.split(',')],
                    'surface details': lambda x: list(reversed(x.split(',')))})

    items = np.unique([item for sublist in df_b['surface details'].values
                       for item in sublist if item not in remove_list]).tolist()
    default_row = {k: 0 for k in items}

    # This is a dataframe where each row is a building and each column is a different rooftip item
    records_vector = []

    for index, row in df_b.iterrows():
        new_row = default_row.copy()
        changes = {item: quantity for quantity, item in zip(row['quantity'], row['surface details']) if item not in remove_list}
        new_row.update(changes)
        records_vector.append(new_row)
    
    df_vec = pd.DataFrame.from_records(records_vector)
    return df_vec

# LevelEditor


This python module allows you to spawn random assets inside of a UE4 world according to requirements you specify in an `assets.json` file with a corresponding map file `map.json`. The `map.json` file is a GEOJSON file that encodes 3D planes in the world to specify where assets are allowed to be spawned.. The `assets.json` specified which assets are allowed to be spawned and configures things such as the random position in 3D planes, rotation, chance of spawning, variability of attributes, etc.  Greater amount of details are provided below.


## `Map.json`

This GeoJSON file looks as follows:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -755.769287109375,
              616.0361328125
            ],
            [
              -1705.769287109375,
              616.0361328125
            ],
            [
              -1705.769287109375,
              1591.0361328125
            ],
            [
              -730.769287109375,
              1591.0361328125
            ],
            [
              -755.769287109375,
              616.0361328125
            ]
          ]
        ]
      },
      "properties": {
        "class_id": 0.0,
        "class_label": "Building_Fake_2",
        "height": 330.0
      }
    },
    ....
}
```
Notice that it is simply a FeatureCollection of 2D **features** which are polygon geometries.  Polygons follow the GeoJSON spec. PLease note the `class_label` property which is useful for filtering. Also note the **mandatory** height label that specifies the height (z value) of the 2D plane on which assets will be placed. Note that the coordinate space is the same as your UE4 coordinate system.

This file is simply an array of features that describe planes on which assets can be randomly spawned. This example is showing a simple 2D geometry that represents a building rooftop at 330 cm above the ground plane. However it can really be anything.  

You may be asking, how will I generate such a file? I personally generate this file by using this  C++ [Point Cloud Plugin](https://github.com/JeremyBYU/PointCloudGeneratorUE4) that generates a **classified** point cloud of your UE4 environment very quickly. It saves a python numpy array with a JSON file specifying the classes.  I then use this python [script](https://github.com/JeremyBYU/create-map) that reads the numpy file to filter and transform this classified point cloud (just a simple numpy array) into the 2D geometries that I desire and output the GeoJSON file. 

## `assets.json`

This JSON file looks like this. Ther are comment annotations that explain some of the spawning behavior of the assets on the feature geometry plane.

```json
{
  "asset_base_path": "/Game/RoofAssets/meshes", // Base path for finding your assets
  "assets": [
    {
      "uid": "small-rooftop-entrance", // some unique name to refer this this asset, like a label
      "asset_details": "BP_Custom_Rooftop_Entrance_Enhanced", // this string is joined with asset_base_path to fully specify asset path
      // This specifies how many assets should be generated
      "quantity": {
        "mean": 10,
        "distribution": "constant" // ['constant', 'exponential']
      },
      // What is the probability of this being placed
      "probability_placement": 1.0,
      // Regex filter to match which feature to place on (feature labels)
      "place_on": ["Building*"],
      // property constraints of the features. must evaluate to true
      // E.g. feature must have property highest_level and be set to true
      // This says only small-rooftop-entrances are only placed on the highest level of a multi-roof building
      "place_on_constraints": ["highest_level"],
      // Rotation of asset are either 0, 90, 180, or 270 degrees
      "rotation": {
        "yaw": [0, 90, 180, 270]
      },
      // Position inside feature control
      "position": {
        // Any static offset to apply after position is determined
        "offset": {
          "z": 0.0
        },
        // Minimum distance the asset should be from border
        "min_dist_from_border": 0.5,
        // 
        "distribution": "normal", // [''normal', 'uniform']
        // only used for normal distribution
        "center": "any", //['any', 'centroid', 'pia']
        "std": 50 
      },
      // manipulate properties, materials, blueprint variables, etc.
      "properties": {
        "Skylight": [true, false], // whether a skylight is added on top of the entrance
        "Material": [  // changes materials
          "Mat_RooftopEnter_Inst",
          "brick_03_Inst",
          "brick_04_Inst",
          "brick_01_Inst",
          "concrete_ground_02_Inst",
          "concrete_ground_03_Inst",
          "Mat_Asphalt_Inst"
        ]
      }
    }
  ]
}
```



# General UE Notes

* Dont duplicate and rename levels. You have to do a copy with drag and drop.*
  * Or use levelgenerator.helper.duplicate_level
* Any source code modifications to levelgenerator require you to restart the Unreal Engine. This is because the module has been loaded and cached. 
  * Its like IPython, but even more difficult to reload changes in module code.
  * This may work `import spawn; reload(spawn.levelgenerator)`




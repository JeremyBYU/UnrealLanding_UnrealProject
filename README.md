# Unreal Landing - Unreal Project

This is a repo containing the Unreal Engine Project for the work in `UnrealLanding`. This project repo is over 13 GB big, so only the source code is included in here. The main source code of interest is the asset placement pipeline in Python. Everything missing resides in the `Content` directory such as:

* Levels
* Meshes
* Materials
* Miscellaneous Assets

None of the raw maps/assets can be redistributed because of licensing issues. However an example full simulation WindowsX64 binary for ONE of the worlds can be downloaded [here](https://drive.google.com/file/d/1UjFg3K7j-Zm0k8iiaxg3RkfWMzxTvUb4/view?usp=sharing). Note that this is only ONE of the many worlds that was generated using the randomized rooftop asset pipeline. Please see the README.md for the asset placement pipeline in `Content/Python/levelgenerator`.


A *test* map/level (loadable in UE4 editor) without any rooftop assets can be found [here](https://drive.google.com/file/d/1UdfcBkOJIA2WSiWwvUXy9Zx65pt3XhJV/view?usp=sharing)


## Plugins
### AirSim Plugin

Please be sure to use the update AirSim Plugin which has an updated LiDAR Sensor model and fixes necessary segmentation codes for the environment. The plugin can be found [here](https://github.com/JeremyBYU/AirSim). Look at the [commit history](https://github.com/JeremyBYU/AirSim/commits/master) for details.

### Point Cloud Generator Plugin

Download a point cloud generation plugin that I created. THis just makes airborne pont clouds of an UE4 environment. Download [here](https://github.com/JeremyBYU/PointCloudGeneratorUE4).

### Python Plugin

You will also need these plugins made by UE4 (Epic). https://docs.unrealengine.com/en-US/ProductionPipelines/ScriptingAndAutomation/Python/index.html

These are built into UE4 and you just need to activate them (Edit -> Plugins).

1. PythonScriptPlugin 
2. EditorScriptingUtilities
3. GLTFImporter



<!-- UnrealLidarSensor.cpp -> getPointCloud. `delta_time`.

*  How much is delta time. 
*  It keeps track of the last azimuth angle scanned. Picks up after
*  It might now have a full point cloud

Updates sensors every tick - Plugins\AirSim\Source\AirLib\include\vehicles\multirotor\MultiRotorPhysicsBody.hpp Line 70

Plugins\AirSim\Source\AirLib\include\sensors\lidar\LidarSimple.hpp -> Line 37


Filee Changes

```
AirSimSettings.hpp
LidarSimSettings.hpp
UnrealLidarSensor.cpp
```

```
10.8 ms for 300,000 points (Debug)
5.6 ms for 300,000 points (Development, Release?)

Actually 11328.....
``` -->


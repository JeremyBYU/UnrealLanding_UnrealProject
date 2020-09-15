# Unreal Landing - Unreal Project

This is a repo containing the Unreal Engine Project for the work in `UnrealLanding`. This project repo is over 13 GB big, so only the source code is included in here. The main source code of interest is the asset placement pipeline in Python. Everything missing resides in the `Content` directory such as:

* Levels
* Meshes
* Materials
* Miscellaneous Assets

None of these binary artifacts can be redistributed because of licensing issues. However an example binary can be distributed and can be found here.


Please see the README.md for the asset placement pipeline in  `Content/Python/levelgenerator`.

## Unreal Lidar Model

UnrealLidarSensor.cpp -> getPointCloud. `delta_time`.

*  How much is delta time. 
*  It keeps track of the last azimuth angle scanned. Picks up after
*  It might now have a full point cloud

Updates sensors every tick - Plugins\AirSim\Source\AirLib\include\vehicles\multirotor\MultiRotorPhysicsBody.hpp Line 70

Plugins\AirSim\Source\AirLib\include\sensors\lidar\LidarSimple.hpp -> Line 37


FIle Changes

```
AirSimSettings.hpp
LidarSimSettings.hpp
UnrealLidarSensor.cpp
```

```
10.8 ms for 300,000 points (Debug)
5.6 ms for 300,000 points (Development, Release?)

Actually 11328.....
```


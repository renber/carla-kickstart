# Carla Kickstart

A thin abstraction on top of the Carla Python API to quickly get started with reproducible simulations.

## Structure

There is one top-level *Simulation* objects which contains several *entities* (vehicles, pedestrians, ...) and an ego-entity. Each entity can have one ore more *Sensor*s and one or more *Behavior*s attached to it.
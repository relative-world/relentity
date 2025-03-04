"""
A collision system.  not a good one, but it's fine.
"""

import argparse
import asyncio
import random
import time

from relentity.core import Entity
from relentity.spatial import Position, Velocity, MovementSystem, SpatialRegistry
from relentity.spatial.physics.systems import CollisionSystem


async def run_benchmark(num_objects=10000, num_steps=1000, check_collisions=False):
    # Create registry
    registry = SpatialRegistry()

    # Create systems
    movement_system = MovementSystem(registry)
    collision_system = CollisionSystem(registry) if check_collisions else None

    # Create entities with random positions and velocities
    print(f"Creating {num_objects} entities...")
    for _ in range(num_objects):
        Entity[
            Position(x=random.uniform(-1000, 1000), y=random.uniform(-1000, 1000)),
            Velocity(vx=random.uniform(-5, 5), vy=random.uniform(-5, 5)),
        ](registry)

    # Run simulation
    print(f"Running simulation for {num_steps} steps...")
    start_time = time.time()

    for step in range(num_steps):
        await movement_system.process()
        if collision_system:
            await collision_system.process()

        if step % 100 == 0:
            print(f"Step {step}/{num_steps}")

    end_time = time.time()
    duration = end_time - start_time

    print(f"\nSimulation completed in {duration:.2f} seconds")
    print(f"Average time per step: {duration / num_steps:.6f} seconds")
    print(f"Objects processed per second: {num_objects * num_steps / duration:.2f}")

    if check_collisions:
        print(f"Total collisions detected: {collision_system.collision_count}")

    return duration


def main():
    parser = argparse.ArgumentParser(description="Relentity performance benchmark")
    parser.add_argument("--objects", type=int, default=1000, help="Number of objects (default: 1000)")
    parser.add_argument("--steps", type=int, default=1000, help="Number of steps (default: 1000)")
    parser.add_argument("--collisions", action="store_true", help="Enable collision detection")

    args = parser.parse_args()

    asyncio.run(run_benchmark(args.objects, args.steps, True))


if __name__ == "__main__":
    main()

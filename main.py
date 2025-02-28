from relentity.components.base import Component
from relentity.entities import Entity
from relentity.registry import Registry
from relentity.systems import System


class Position(Component):
    x: float
    y: float


class Velocity(Component):
    vx: float
    vy: float


class MovementSystem(System):
    def update(self):
        entities = self.registry.get_entities_with_components(Position, Velocity)
        for entity in entities:
            position = entity.get_component(Position)
            velocity = entity.get_component(Velocity)
            position.x += velocity.vx
            position.y += velocity.vy


def main():
    registry = Registry()

    entity = Entity[
        Position(x=0, y=0),
        Velocity(vx=1, vy=1)
    ](registry)

    NewPlayer = Entity[
        Position(x=0, y=0),
        Velocity(vx=0, vy=0)
    ]

    NewPlayer(registry)

    # Alternatively
    entity = Entity(registry)
    entity.add_component(Position(x=0, y=0))
    entity.add_component(Velocity(vx=1, vy=1))

    movement_system = MovementSystem(registry)
    movement_system.update()

    print(entity.get_component(Position))


if __name__ == "__main__":
    main()

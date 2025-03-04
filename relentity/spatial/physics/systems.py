from relentity.core import System
from relentity.spatial import Position, Velocity
from relentity.spatial.physics.components import ShapeBody, ShapeType


class CollisionSystem(System):
    def __init__(self, registry):
        super().__init__(registry)
        self.collision_count = 0

    async def update(self, delta_time: float = 0) -> None:
        entities_data = []

        # Collect all entities with position, velocity, and renderable shape
        async for entity_ref in self.registry.entities_with_components(Position, Velocity, ShapeBody):
            entity = await entity_ref.resolve()
            if entity:
                position = await entity.get_component(Position)
                velocity = await entity.get_component(Velocity)
                shape = await entity.get_component(ShapeBody)
                entities_data.append((entity, position, velocity, shape))

        if not entities_data:
            return

        # Check for collisions between all entity pairs
        for i in range(len(entities_data)):
            entity1, pos1, vel1, shape1 = entities_data[i]

            for j in range(i + 1, len(entities_data)):
                entity2, pos2, vel2, shape2 = entities_data[j]

                # Check for collision based on shape types
                if self._check_collision(pos1, shape1, pos2, shape2):
                    self.collision_count += 1

                    # More natural collision response
                    # Calculate collision normal vector
                    dx = pos2.x - pos1.x
                    dy = pos2.y - pos1.y
                    distance = (dx * dx + dy * dy) ** 0.5

                    if distance > 0:  # Avoid division by zero
                        # Normalize the collision normal
                        nx = dx / distance
                        ny = dy / distance

                        # Calculate relative velocity along normal
                        dvx = vel2.vx - vel1.vx
                        dvy = vel2.vy - vel1.vy
                        normal_vel = dvx * nx + dvy * ny

                        # Only separate if objects are moving toward each other
                        if normal_vel < 0:
                            # Assume equal masses (can be extended with a Mass component)
                            mass_ratio1 = 0.5
                            mass_ratio2 = 0.5

                            # Impulse scalar
                            j = -(1 + 0.8) * normal_vel  # 0.8 = coefficient of restitution

                            # Apply impulse
                            impulse_x = j * nx
                            impulse_y = j * ny

                            vel1.vx -= impulse_x * mass_ratio1
                            vel1.vy -= impulse_y * mass_ratio1
                            vel2.vx += impulse_x * mass_ratio2
                            vel2.vy += impulse_y * mass_ratio2

                            # Optional: add a bit of position correction to prevent sinking
                            penetration = 0.05  # small constant to prevent objects from sticking
                            vel1.vx -= nx * penetration
                            vel1.vy -= ny * penetration
                            vel2.vx += nx * penetration
                            vel2.vy += ny * penetration

    def _check_collision(self, pos1, shape1, pos2, shape2):
        """Check for collision between two entities based on their shapes"""
        # Circle-Circle collision
        if shape1.shape_type == ShapeType.CIRCLE and shape2.shape_type == ShapeType.CIRCLE:
            distance_squared = (pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2
            min_distance = shape1.radius + shape2.radius
            return distance_squared < min_distance**2

        # Rectangle-Rectangle collision (AABB)
        elif shape1.shape_type == ShapeType.RECTANGLE and shape2.shape_type == ShapeType.RECTANGLE:
            return not (
                pos1.x + shape1.width / 2 < pos2.x - shape2.width / 2
                or pos1.x - shape1.width / 2 > pos2.x + shape2.width / 2
                or pos1.y + shape1.height / 2 < pos2.y - shape2.height / 2
                or pos1.y - shape1.height / 2 > pos2.y + shape2.height / 2
            )

        # Circle-Rectangle collision
        elif shape1.shape_type == ShapeType.CIRCLE and shape2.shape_type == ShapeType.RECTANGLE:
            return self._check_circle_rectangle(pos1, shape1.radius, pos2, shape2.width, shape2.height)
        elif shape1.shape_type == ShapeType.RECTANGLE and shape2.shape_type == ShapeType.CIRCLE:
            return self._check_circle_rectangle(pos2, shape2.radius, pos1, shape1.width, shape1.height)

        # Default to a simple distance check for other shapes (including triangles)
        # This is a simplification - for triangles we use the radius as an approximation
        else:
            radius1 = getattr(shape1, "radius", 10)
            radius2 = getattr(shape2, "radius", 10)
            distance_squared = (pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2
            return distance_squared < (radius1 + radius2) ** 2

    def _check_circle_rectangle(self, circle_pos, circle_radius, rect_pos, rect_width, rect_height):
        """Check for collision between a circle and a rectangle"""
        # Find closest point on rectangle to circle
        closest_x = max(rect_pos.x - rect_width / 2, min(circle_pos.x, rect_pos.x + rect_width / 2))
        closest_y = max(rect_pos.y - rect_height / 2, min(circle_pos.y, rect_pos.y + rect_height / 2))

        # Calculate distance from closest point to circle center
        distance_squared = (circle_pos.x - closest_x) ** 2 + (circle_pos.y - closest_y) ** 2

        return distance_squared < circle_radius**2

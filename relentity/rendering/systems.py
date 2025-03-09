import time

import pygame

from relentity.core.exceptions import UnknownEntityError
from relentity.core.systems import System
from relentity.rendering.components import (
    RenderableShape,
    RenderableColor,
    ShapeType,
    RenderLayer,
    SpeechBubble,
    RenderableImage,
    VelocityFacingImage,
    AnimatedSprite,
)
from relentity.spatial.components import Position, Velocity


def wrap_text(text, font, max_width):
    """Wrap text to fit within a specified width."""
    words = text.split(" ")
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        width, _ = font.size(" ".join(current_line))
        if width > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]

    lines.append(" ".join(current_line))
    return lines


class RenderSystem(System):
    """System that renders entities with visual components to a pygame surface."""

    def __init__(self, registry, width=800, height=600, title="Relentity Simulation"):
        super().__init__(registry)
        self.width = width
        self.height = height
        self.title = title
        self.screen = None
        self.running = False
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 0.75

    async def initialize(self) -> None:
        """Initialize pygame and create the display window."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.running = True

    async def update(self, delta_time: float = 0) -> None:
        """Render all entities with visual components."""
        if not self.running:
            return

        # Process pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                return

        # Clear the screen
        self.screen.fill((0, 0, 0))

        # Get all renderable entities grouped by layer
        render_layers = {}
        async for entity_ref in self.registry.entities_with_components(Position):
            try:
                entity = await entity_ref.resolve()
                position = await entity.get_component(Position)

                # Get layer (use default if not present)
                layer = 0
                layer_component = await entity.get_component(RenderLayer)
                if layer_component:
                    layer = layer_component.layer

                if layer not in render_layers:
                    render_layers[layer] = []

                # Check for VelocityFacingImage first
                velocity_facing_image = await entity.get_component(VelocityFacingImage)
                if velocity_facing_image:
                    velocity = await entity.get_component(Velocity)
                    if velocity:
                        velocity_facing_image.update_rotation(velocity)
                    render_layers[layer].append(("velocity_image", entity, position, velocity_facing_image))
                    continue

                # Check for AnimatedSprite
                animated_sprite = await entity.get_component(AnimatedSprite)
                if animated_sprite:
                    animated_sprite.update(delta_time)
                    render_layers[layer].append(("animated_sprite", entity, position, animated_sprite))
                    continue

                # Check for RenderableImage
                image_component = await entity.get_component(RenderableImage)
                if image_component:
                    render_layers[layer].append(("image", entity, position, image_component))
                    continue

                # Check for RenderableShape
                shape = await entity.get_component(RenderableShape)
                if shape:
                    # Get color (use default if not present)
                    color = (255, 255, 255, 255)
                    color_component = await entity.get_component(RenderableColor)
                    if color_component:
                        color = color_component.rgba

                    render_layers[layer].append(("shape", entity, position, shape, color))
            except UnknownEntityError:
                # Entity might have been removed by another system between the query and resolution
                continue

        # Render entities layer by layer
        for layer in sorted(render_layers.keys()):
            for item in render_layers[layer]:
                entity_type = item[0]
                entity = item[1]
                position = item[2]

                if entity_type == "velocity_image":
                    velocity_facing_image = item[3]
                    image = velocity_facing_image.get_image()
                    screen_x = int((position.x - self.camera_x) * self.zoom + self.width / 2 - image.get_width() / 2)
                    screen_y = int((position.y - self.camera_y) * self.zoom + self.height / 2 - image.get_height() / 2)
                    self.screen.blit(image, (screen_x, screen_y))

                elif entity_type == "animated_sprite":
                    animated_sprite = item[3]

                    # Update rotation based on velocity if needed
                    if animated_sprite.velocity_facing:
                        velocity = await entity.get_component(Velocity)
                        if velocity:
                            animated_sprite.update_rotation(velocity)

                    frame = animated_sprite.get_current_frame()
                    if frame:
                        screen_x = int(
                            (position.x - self.camera_x) * self.zoom + self.width / 2 - frame.get_width() / 2
                        )
                        screen_y = int(
                            (position.y - self.camera_y) * self.zoom + self.height / 2 - frame.get_height() / 2
                        )
                        self.screen.blit(frame, (screen_x, screen_y))

                elif entity_type == "image":
                    image_component = item[3]
                    image = image_component.get_image()
                    screen_x = int((position.x - self.camera_x) * self.zoom + self.width / 2 - image.get_width() / 2)
                    screen_y = int((position.y - self.camera_y) * self.zoom + self.height / 2 - image.get_height() / 2)
                    self.screen.blit(image, (screen_x, screen_y))

                elif entity_type == "shape":
                    shape = item[3]
                    color = item[4]

                    # Convert world coordinates to screen coordinates
                    screen_x = int((position.x - self.camera_x) * self.zoom + self.width / 2)
                    screen_y = int((position.y - self.camera_y) * self.zoom + self.height / 2)

                    # Render based on shape type
                    if shape.shape_type == ShapeType.CIRCLE:
                        radius = int(shape.radius * self.zoom)
                        pygame.draw.circle(self.screen, color, (screen_x, screen_y), radius)
                    elif shape.shape_type == ShapeType.RECTANGLE:
                        width = int(shape.width * self.zoom)
                        height = int(shape.height * self.zoom)
                        rect = pygame.Rect(screen_x - width // 2, screen_y - height // 2, width, height)
                        pygame.draw.rect(self.screen, color, rect)
                    elif shape.shape_type == ShapeType.TRIANGLE:
                        radius = int(shape.radius * self.zoom)
                        points = [
                            (screen_x, screen_y - radius),
                            (screen_x - radius, screen_y + radius),
                            (screen_x + radius, screen_y + radius),
                        ]
                        pygame.draw.polygon(self.screen, color, points)

                # Render speech bubble if present
                speech_bubble = await entity.get_component(SpeechBubble)
                if speech_bubble and time.time() - speech_bubble.start_time < speech_bubble.duration:
                    font = pygame.font.Font(None, 24)
                    max_width = 200  # Maximum width of the speech bubble
                    wrapped_lines = wrap_text(speech_bubble.text, font, max_width)
                    bubble_height = len(wrapped_lines) * font.get_linesize()

                    # For shapes
                    if entity_type == "shape":
                        height = int(
                            shape.radius * 2 if shape.shape_type == ShapeType.CIRCLE else shape.height * self.zoom
                        )
                    # For images
                    else:
                        height = image_component.get_image().get_height()

                    bubble_rect = pygame.Rect(
                        screen_x - max_width // 2 - 5,
                        screen_y - height - bubble_height - 25,
                        max_width + 10,
                        bubble_height + 10,
                    )
                    for i, line in enumerate(wrapped_lines):
                        text_surface = font.render(line, True, (255, 255, 255))
                        self.screen.blit(text_surface, (bubble_rect.x + 5, bubble_rect.y + 5 + i * font.get_linesize()))

        # Update the display
        pygame.display.flip()

    async def shutdown(self) -> None:
        """Clean up pygame resources."""
        if pygame.get_init():
            pygame.quit()

import math
import time
from enum import Enum
from typing import Tuple, Annotated

import pygame
from pydantic import PrivateAttr, Field

from relentity.core.components import Component


class ShapeType(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"


class RenderableShape(Component):
    shape_type: ShapeType = ShapeType.CIRCLE
    radius: int = 10  # For circles
    width: int = 20  # For rectangles
    height: int = 20  # For rectangles


class RenderableColor(Component):
    r: int = 255
    g: int = 255
    b: int = 255
    alpha: int = 255

    @property
    def rgba(self) -> Tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.alpha)


class RenderLayer(Component):
    layer: int = 0  # Higher layers render on top


class RenderableImage(Component):
    """Component that renders an image for an entity"""

    image_path: str  # Path to the image file
    width: int = None  # Width for scaling (None = use original)
    height: int = None  # Height for scaling (None = use original)
    flip_x: bool = False  # Whether to flip horizontally
    flip_y: bool = False  # Whether to flip vertically
    rotation: float = 0.0  # Rotation in degrees
    _image: pygame.Surface = None  # Cached pygame surface

    def get_image(self):
        """Load and cache the image"""
        if self._image is None:
            self._image = pygame.image.load(self.image_path).convert_alpha()

            # Scale if dimensions provided
            if self.width is not None and self.height is not None:
                self._image = pygame.transform.scale(self._image, (self.width, self.height))

        # Handle flipping and rotation if needed
        image = self._image
        if self.flip_x or self.flip_y:
            image = pygame.transform.flip(image, self.flip_x, self.flip_y)
        if self.rotation != 0:
            image = pygame.transform.rotate(image, self.rotation)

        return image


class VelocityFacingImage(RenderableImage):
    """Component that renders an image facing the direction of movement"""

    base_rotation: float = 0.0  # Offset angle if image has a different default orientation

    def update_rotation(self, velocity):
        """Update rotation based on velocity vector"""
        if velocity.vx != 0 or velocity.vy != 0:
            # Calculate angle in degrees from velocity vector
            # atan2 returns radians, convert to degrees
            angle = math.degrees(math.atan2(velocity.vy, velocity.vx))

            # Invert the angle to correct the rotation
            angle = -angle

            # Add 90 degrees because pygame's 0 degree is right-facing
            # and we typically want 0 to be up-facing
            self.rotation = angle - 90 + self.base_rotation


class SpeechBubble(Component):
    text: str
    duration: float  # Duration in seconds
    start_time: float  # Time when the speech bubble was created


class AnimatedSprite(Component):
    """Component for animated sprites with different animation states"""

    animations: dict  # Dictionary mapping state names to lists of image paths
    current_state: str  # Current animation state
    frame_duration: float = 0.1  # Time per frame in seconds
    current_frame: int = 0  # Current frame index
    width: int = None  # Width for scaling
    height: int = None  # Height for scaling
    flip_x: bool = False  # Whether to flip horizontally
    flip_y: bool = False  # Whether to flip vertically
    rotation: float = 0.0  # Rotation in degrees
    velocity_facing: bool = False  # Whether to rotate based on velocity
    base_rotation: float = 0.0  # Offset angle if image has a different default orientation
    last_frame_time: Annotated[float, Field(default_factory=time.time)]  # Time when the last frame was displayed
    _loaded_frames: Annotated[dict, PrivateAttr()] = {}  # Cache for loaded images

    def update_rotation(self, velocity):
        """Update rotation based on velocity vector"""
        if self.velocity_facing and (velocity.vx != 0 or velocity.vy != 0):
            # Calculate angle in degrees from velocity vector
            angle = math.degrees(math.atan2(velocity.vy, velocity.vx))

            # Invert the angle to correct the rotation
            angle = -angle

            # Subtract 90 degrees because pygame's 0 degree is right-facing
            # and we typically want 0 to be up-facing
            self.rotation = angle - 90 + self.base_rotation

    def get_current_frame(self):
        """Get the current frame of the current animation state"""
        if self.current_state not in self.animations:
            return None

        frame_paths = self.animations[self.current_state]
        if not frame_paths:
            return None

        # Load frames if needed
        if self.current_state not in self._loaded_frames:
            self._loaded_frames[self.current_state] = []
            for path in frame_paths:
                image = pygame.image.load(path).convert_alpha()
                if self.width is not None and self.height is not None:
                    image = pygame.transform.scale(image, (self.width, self.height))
                self._loaded_frames[self.current_state].append(image)

        # Get the current frame
        frames = self._loaded_frames[self.current_state]
        frame = frames[self.current_frame % len(frames)]

        # Handle flipping and rotation
        if self.flip_x or self.flip_y:
            frame = pygame.transform.flip(frame, self.flip_x, self.flip_y)
        if self.rotation != 0:
            frame = pygame.transform.rotate(frame, self.rotation)

        return frame

    def update(self, delta_time):
        """Update the animation state"""
        current_time = time.time()
        if current_time - self.last_frame_time > self.frame_duration:
            self.current_frame += 1
            self.last_frame_time = current_time

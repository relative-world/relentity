from relentity.core import Component


class PlayerControlled(Component):
    """Component that marks an entity as player-controlled"""

    speed: float = 200.0


class TerrainChunk(Component):
    """Component for a terrain chunk containing multiple tiles"""

    chunk_x: int
    chunk_y: int
    # Other chunk metadata as needed

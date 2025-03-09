from relentity.ai import ToolEnabledComponent, tool, AIDriven
from relentity.core import Component, Entity, Identity
from relentity.spatial import Position, Area
from relentity.spatial.events import AreaEvent, AREA_ENTERED_EVENT_TYPE, AREA_EXITED_EVENT_TYPE
from relentity.spatial.sound.components import Audible
from relentity.spatial.vision.components import Visible
from relentity.rendering.components import RenderableColor, RenderableShape, ShapeType, RenderLayer


class FireTools(ToolEnabledComponent):
    @tool
    async def light_fire(self, actor) -> str:
        """Light the fire in the fire pit"""
        fire_pit = await self._fire_pit_ref.resolve()
        fire_pit_component = await fire_pit.get_component(FirePit)
        visible_component = await fire_pit.get_component(Visible)

        if fire_pit_component.is_lit:
            return "The fire is already lit."

        fire_pit_component.is_lit = True

        # Update visual appearance
        visual = await fire_pit.get_component(RenderableColor)
        visual.r, visual.g, visual.b = 255, 100, 0  # Orange-red glow

        visible_component.description = "A roaring fire in a fire pit, providing warmth and light."

        return "You've lit the fire. The flames crackle and provide warmth."

    @tool
    async def put_out_fire(self, actor) -> str:
        """Put out the fire in the fire pit"""
        fire_pit = await self._fire_pit_ref.resolve()
        fire_pit_component = await fire_pit.get_component(FirePit)
        visible_component = await fire_pit.get_component(Visible)

        if not fire_pit_component.is_lit:
            return "The fire is already out."

        fire_pit_component.is_lit = False

        # Update visual appearance
        visual = await fire_pit.get_component(RenderableColor)
        visual.r, visual.g, visual.b = 50, 50, 50  # Dark gray

        visible_component.description = (
            "A well stocked firepit, ready to make a fire.  Wood and fire starting materials are already here."
        )

        return "You've extinguished the fire."


class FirePit(Component):
    """Component representing a fire pit that can be lit or extinguished"""

    is_lit: bool = False

    async def handle_area_entered(self, event: AreaEvent):
        entity = await event.entity_ref.resolve()

        # Check if the entity is AI-driven
        ai_driven = await entity.get_component(AIDriven)
        if ai_driven:
            # Add fire tools to the entity
            fire_tools = FireTools()
            fire_tools._fire_pit_ref = event.area_entity_ref
            await entity.add_component(fire_tools)

            # Update the AI's extra_tools dictionary
            ai_driven.extra_tools.update(fire_tools._tools)

    async def handle_area_exited(self, event: AreaEvent):
        entity = await event.entity_ref.resolve()

        # Check if the entity is AI-driven
        ai_driven = await entity.get_component(AIDriven)
        if ai_driven:
            fire_tools = await entity.get_component(FireTools)

            # Remove the tools from AI's extra_tools
            for tool_name in fire_tools._tools:
                ai_driven.extra_tools.pop(tool_name, None)

            await entity.remove_component(FireTools)


async def create_fire_pit(registry, x=0, y=0, radius=50):
    """Create a fire pit entity that provides fire tools to AI entities"""

    buffered_radius = radius + 50
    fire_pit = Entity[
        Identity(
            name="The Fire Pit",
            description="A well stocked firepit, ready to make a fire.  A great place to make camp.  Wood and fire starting materials are already here.",
        ),
        Position(x=x, y=y),
        Area(
            center_point=(x, y),
            geometry=[
                (x - buffered_radius, y - buffered_radius),
                (x, y + buffered_radius),
                (x + buffered_radius, y - buffered_radius),
                (x, y - buffered_radius),
            ],
        ),
        Visible(
            description="A well stocked firepit, ready to make a fire.  A great place to make camp.  Wood and fire starting materials are already here."
        ),
        Audible(volume=20),
        RenderableShape(shape_type=ShapeType.RECTANGLE, radius=radius, width=radius, height=radius),
        RenderableColor(r=50, g=50, b=50),  # Start with gray (unlit)
        RenderLayer(layer=0),
        FirePit(),
    ](registry)

    # Register event handlers
    fire_pit_component = await fire_pit.get_component(FirePit)
    fire_pit.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, fire_pit_component.handle_area_entered)
    fire_pit.event_bus.register_handler(AREA_EXITED_EVENT_TYPE, fire_pit_component.handle_area_exited)

    return fire_pit

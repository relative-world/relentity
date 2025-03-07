import random
import time

from examples.ai.inventories.controllers import AIMovementController
from relentity.ai import TextPromptComponent, AIDriven, AI_RESPONSE_EVENT_TYPE
from relentity.ai.systems import EmotiveResponse
from relentity.core import Identity
from relentity.spatial import Position, Velocity
from relentity.spatial.events import (
    ENTITY_SEEN_EVENT_TYPE,
    SOUND_HEARD_EVENT_TYPE,
    SOUND_CREATED_EVENT_TYPE,
    AREA_ENTERED_EVENT_TYPE,
    AREA_EXITED_EVENT_TYPE,
    SoundEvent,
)
from relentity.spatial.physics.components import ShapeBody, ShapeType as BodyShapeType
from relentity.spatial.sensory.components import Vision, Visible, Audible, Hearing
from relentity.tasks import TaskedEntity
from relentity.visual.components import RenderableShape, ShapeType, RenderableColor, RenderLayer, SpeechBubble


class Actor(TaskedEntity):
    def __init__(
        self,
        registry,
        name,
        description,
        width,
        color,
        *args,
        location=None,
        private_info=None,
        model="qwen2.5:3b",
        **kwargs,
    ):
        super().__init__(registry, *args, **kwargs)
        location = location or (random.randint(-200, 200), random.randint(-100, 100))
        components = [
            Identity(name=name, description=description),
            Position(x=location[0], y=location[1]),
            Velocity(vx=0, vy=0),
            TextPromptComponent(text=private_info) if private_info else None,
            AIMovementController(),
            Vision(max_range=1000),
            Visible(description=f"{name} - {description}"),
            Audible(volume=400),
            Hearing(volume=400),
            AIDriven(model=model, update_interval=1),
            RenderableShape(shape_type=ShapeType.CIRCLE, radius=width // 2),
            RenderableColor(r=color[0], g=color[1], b=color[2]),
            RenderLayer(layer=1),
            ShapeBody(
                shape_type=BodyShapeType.CIRCLE,
                radius=width // 2,
            ),
            SpeechBubble(text=f"{name} - {description}", duration=10.0, start_time=time.time()),
        ]
        for component in components:
            if component:
                self.add_component_sync(component)

        self.event_bus.register_handler(AI_RESPONSE_EVENT_TYPE, self.on_ai_response)
        self.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, self.on_entity_seen)
        self.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, self.on_sound_heard_event)
        self.event_bus.register_handler(SOUND_CREATED_EVENT_TYPE, self.on_sound_created_event)
        self.event_bus.register_handler("goal.added", self.on_goal_added)
        self.event_bus.register_handler("goal.complete", self.on_goal_complete)
        self.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, self.on_area_entered)
        self.event_bus.register_handler(AREA_EXITED_EVENT_TYPE, self.on_area_exited)

    async def on_entity_seen(self, event):
        if event.entity_ref.entity_id is self.id:
            return
        ai_driven = await self.get_component(AIDriven)
        await ai_driven.add_event_for_consideration(ENTITY_SEEN_EVENT_TYPE, event, hash_key=event.entity_ref.entity_id)

    async def on_ai_response(self, response: EmotiveResponse):
        audio = await self.get_component(Audible)
        if response.speech:
            sound_event = SoundEvent(self.entity_ref, "speech", response.speech)
            audio.queue_sound(sound_event)

    async def on_sound_heard_event(self, sound_event):
        ai_driven = await self.get_component(AIDriven)
        await ai_driven.add_event_for_consideration(SOUND_HEARD_EVENT_TYPE, sound_event)

    async def on_sound_created_event(self, sound_event):
        ai_driven = await self.get_component(AIDriven)
        # Add speech bubble component
        speech_bubble = SpeechBubble(text=sound_event.sound, duration=5.0, start_time=time.time())
        await self.add_component(speech_bubble)
        await ai_driven.add_event_for_consideration(SOUND_CREATED_EVENT_TYPE, sound_event)

    async def on_goal_added(self, event):
        print("added", event)

    async def on_goal_complete(self, event):
        print("completed", event)

    async def on_area_entered(self, event):
        print(self, "entered", event)

    async def on_area_exited(self, event):
        print(self, "exited", event)

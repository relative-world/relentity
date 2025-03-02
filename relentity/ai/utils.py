from relentity.core import Identity
from relentity.spatial import Visible, SOUND_HEARD_EVENT_TYPE, SOUND_CREATED_EVENT_TYPE


async def pretty_name_entity(entity):
    """
    Retrieves the pretty name of an entity.

    Args:
        entity (Entity): The entity to get the name of.

    Returns:
        str: The name of the entity, or its representation if it has no Identity component.
    """
    ident = await entity.get_component(Identity)
    if ident:
        return ident.name
    else:
        return repr(entity)


async def pretty_print_event(event_type: str, data, past_tense=False):
    """
    Pretty prints an event based on its type and data.

    Args:
        event_type (str): The type of the event.
        data (Any): The data associated with the event.
        past_tense (bool, optional): Whether to format the event in past tense. Defaults to False.

    Returns:
        str: The pretty printed event description.
    """
    if event_type == "position_updated":
        return f"Position updated to ({data.x}, {data.y})"
    elif event_type == "entity_seen":
        entity_name = await pretty_name_entity(data.entity)
        description = (await data.entity.get_component(Visible)).description
        position = data.position
        velocity = data.velocity
        if past_tense:
            result = f"You last saw {entity_name} at ({position.x}, {position.y}) - ({description})"
        else:
            result = f"You see {entity_name} is at ({position.x}, {position.y}) - ({description})"
        if velocity is not None:
            result += f" moving at velocity ({velocity.vx}, {velocity.vy})"
        return result
    elif event_type == "task.progress":
        return f"Task progress: {data.task} - {data.remaining_cycles} cycles remaining"
    elif event_type == "task.complete":
        return f"Task complete: {data.task}"
    elif event_type == "task.abandoned":
        return f"Task abandoned: {data.task} - {data.remaining_cycles} cycles remained"
    elif event_type == SOUND_HEARD_EVENT_TYPE:
        entity_name = await pretty_name_entity(data.entity)
        return f"Sound heard: source={entity_name}, sound={data.sound}, type={data.sound_type}"
    elif event_type == SOUND_CREATED_EVENT_TYPE:
        return f"You said: {data.sound}"
    else:
        return f"Event type: {event_type} with data: {data}"

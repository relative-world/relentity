import random
import time

from relentity.ai import ToolEnabledComponent, tool
from relentity.ai.cognition.components import (
    PerceptionComponent,
    MemoryComponent,
    BeliefSystemComponent,
    RelationshipComponent,
    EmotionalStateComponent,
    GoalComponent,
    MetaCognitionComponent,
)
from relentity.ai.cognition.models import GoalPriority, RelationshipType, EmotionType, CognitiveAction
from relentity.ai.cognition.systems import CognitiveSystem
from relentity.core import Entity, Registry, Component, System
from relentity.spatial import Position, Velocity, MovementSystem
import pygame
import pygame.freetype

from relentity.tasks import Task

import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel

from relentity.ai.pydantic_ollama.client import PydanticOllamaClient
from relentity.settings import settings
from relentity.ai.cognition.components import CognitiveComponent


class CognitiveResponse(BaseModel):
    """Model for structured responses from the LLM for cognitive processing"""

    analysis: str
    action: CognitiveAction
    reasoning: str


class CognitiveProcessingSystem(System):
    """System for processing cognitive cycles using LLM"""

    def __init__(self, registry):
        super().__init__(registry)
        self._client = PydanticOllamaClient(settings.base_url, settings.default_model)
        self._processing_entities = set()
        self.update_interval = 2.0  # Run cognitive cycles every 2 seconds

    async def update(self, delta_time: float = 0) -> None:
        """Process entities with cognitive components"""
        async for entity_ref in self.registry.entities_with_components(CognitiveComponent):
            entity = await entity_ref.resolve()

            # Skip entities already being processed
            if entity.id in self._processing_entities:
                continue

            # Mark entity as being processed
            self._processing_entities.add(entity.id)

            # Process asynchronously
            task = asyncio.create_task(self.process_cognitive_entity(entity))
            task.add_done_callback(lambda t, eid=entity.id: self._processing_entities.discard(eid))

    async def process_cognitive_entity(self, entity):
        """Process cognitive cycle for an entity with LLM assistance"""
        cognitive = await entity.get_component(CognitiveComponent)

        # Check if it's time to run a cycle
        current_time = time.time()
        if current_time - cognitive.last_processed_time < cognitive.cognitive_cycle_interval:
            return

        cognitive.last_processed_time = current_time
        cognitive.processing_state = "processing"

        try:
            # Generate prompts from perceptions and cognitive state
            system_prompt = await self._generate_system_prompt(entity)
            prompt = await self._generate_prompt(entity)

            # Call the LLM
            _, response = await self._client.generate(
                prompt=prompt, system=system_prompt, response_model=CognitiveResponse
            )

            # Process the LLM response
            if response:
                cognitive.inferred_situation = {"analysis": response.analysis}

                # Execute the action if provided
                if response.action:
                    cognitive.last_action = response.action
                    await self._execute_action(entity, response.action)

        except Exception as e:
            print(f"Error in cognitive processing for entity {entity.id}: {e}")
        finally:
            cognitive.processing_state = "idle"

    async def _generate_system_prompt(self, entity) -> str:
        """Generate a system prompt for cognitive processing"""
        return (
            "You are the cognitive core of an AI entity in a simulation. "
            "Your role is to perceive the environment, interpret the situation, "
            "make decisions, and determine appropriate actions. "
            "Respond with a thoughtful analysis of the current situation, "
            "and determine what action the entity should take next. "
            "Your response should follow the CognitiveResponse format with an analysis, "
            "an action specification, and reasoning."
        )

    async def _generate_prompt(self, entity) -> str:
        """Generate a prompt describing the current situation for cognitive processing"""
        # Get perception data
        perception = await entity._process_perception(entity)

        # Format the prompt
        prompt = f"Current perceptions: {perception}\n\n"

        # Add memory information if available
        memory = await entity.get_component(MemoryComponent)
        if memory:
            # Get some relevant memories
            goal_component = await entity.get_component(GoalComponent)
            if goal_component:
                current_goal = await goal_component.get_highest_priority_goal()
                if current_goal:
                    memories = await memory.retrieve_relevant_memories(current_goal.description, limit=3)
                    prompt += f"Relevant memories: {memories}\n\n"

        # Add current goal
        goal_component = await entity.get_component(GoalComponent)
        if goal_component:
            current_goal = await goal_component.get_highest_priority_goal()
            if current_goal:
                prompt += f"Current goal: {current_goal.description}\n"

        return prompt

    async def _execute_action(self, entity, action):
        """Execute the action decided by the cognitive process"""
        # This would typically update component states or emit events
        print(f"Entity {entity.id} executing: {action.action_type} - {action.reasoning}")

        # Example implementation for movement actions
        if action.action_type in ["approach", "flee", "explore"]:
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)

            if position and velocity:
                # Handle movement actions (similar logic to current _execute_action)
                # For brevity, movement logic isn't duplicated here
                pass


class MovementTask(Task):
    task: str = "moving to coordinates"
    target_x: float
    target_y: float
    speed: float = 50.0
    proximity_threshold: float = 5.0
    remaining_cycles: int = 100  # Will be completed when reaching target


class AIMovementController(ToolEnabledComponent):
    @tool
    async def stop_movement(self, actor):
        velocity = await actor.get_component(Velocity)
        if velocity:
            velocity.vx = 0
            velocity.vy = 0

    @tool
    async def go_to_coordinates(self, actor, x: float, y: float) -> str:
        """Move to the specified coordinates"""
        # Create and assign a movement task
        movement_task = MovementTask(target_x=x, target_y=y)
        await actor.set_task(movement_task)
        return f"Moving to coordinates ({x}, {y})"


class MovementTaskSystem(System):
    async def update(self, delta_time: float = 0) -> None:
        async for entity_ref in self.registry.entities_with_components(MovementTask, Position, Velocity):
            entity = await entity_ref.resolve()
            task = await entity.get_component(MovementTask)
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)

            if not task:
                continue

            # Calculate direction to target
            dx = task.target_x - position.x
            dy = task.target_y - position.y
            distance = (dx**2 + dy**2) ** 0.5

            # Check if we've reached the target
            if distance <= task.proximity_threshold:
                # Stop movement
                velocity.vx = 0
                velocity.vy = 0
                # Complete the task
                task.remaining_cycles = 0
            else:
                # Update velocity toward target
                if distance > 0:
                    velocity.vx = task.speed * dx / distance
                    velocity.vy = task.speed * dy / distance


class RenderSystem(System):
    """System for rendering the scavenger hunt simulation using Pygame."""

    def __init__(self, registry, width=800, height=800):
        super().__init__(registry)
        self.width = width
        self.height = height
        self.scale_factor = min(width, height) / 100  # Convert from simulation units to pixels

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Scavenger Hunt Simulation")
        self.font = pygame.freetype.SysFont("Arial", 12)
        self.clock = pygame.time.Clock()

        # Define colors and entity visuals
        self.colors = {
            "background": (240, 240, 240),
            "grid": (200, 200, 200),
            "hunter": (50, 100, 200),
            "gold_coin": (255, 215, 0),
            "silver_key": (192, 192, 192),
            "ancient_scroll": (222, 184, 135),
            "magic_crystal": (147, 112, 219),
            "rusty_dagger": (139, 69, 19),
            "text": (10, 10, 10),
        }

        # Size of entities in pixels
        self.hunter_size = 12
        self.item_size = 8

    def _world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates."""
        return int(x * self.scale_factor), int(y * self.scale_factor)

    async def update(self, delta_time: float = 0) -> None:
        """Render the current state of the simulation."""
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys

                sys.exit()

        # Clear screen
        self.screen.fill(self.colors["background"])

        # Draw grid lines
        for i in range(0, 101, 10):
            pos = i * self.scale_factor
            # Vertical line
            pygame.draw.line(self.screen, self.colors["grid"], (pos, 0), (pos, self.height), 1)
            # Horizontal line
            pygame.draw.line(self.screen, self.colors["grid"], (0, pos), (self.width, pos), 1)

        # Draw collectibles
        async for entity_ref in self.registry.entities_with_components(CollectibleComponent, Position):
            entity = await entity_ref.resolve()
            collectible = await entity.get_component(CollectibleComponent)
            position = await entity.get_component(Position)

            if not collectible.collected:
                color = self.colors.get(collectible.name, (100, 100, 100))
                screen_x, screen_y = self._world_to_screen(position.x, position.y)
                pygame.draw.circle(self.screen, color, (screen_x, screen_y), self.item_size)

                # Draw item name
                self.font.render_to(
                    self.screen, (screen_x - 15, screen_y - 15), collectible.name[:3], self.colors["text"]
                )

        # Draw hunters
        async for entity_ref in self.registry.entities_with_components(InventoryComponent, Position):
            entity = await entity_ref.resolve()
            position = await entity.get_component(Position)
            inventory = await entity.get_component(InventoryComponent)
            emotional = await entity.get_component(EmotionalStateComponent)

            screen_x, screen_y = self._world_to_screen(position.x, position.y)

            # Draw hunter
            pygame.draw.circle(self.screen, self.colors["hunter"], (screen_x, screen_y), self.hunter_size)

            # Draw inventory count
            total_value = await inventory.get_total_value()
            self.font.render_to(self.screen, (screen_x - 5, screen_y - 20), f"${total_value}", self.colors["text"])

            # Draw emotion indicator
            emotion_color = (
                (0, 255, 0)
                if emotional.dominant_emotion == EmotionType.JOY
                else (255, 0, 0)
                if emotional.dominant_emotion == EmotionType.ANGER
                else (255, 255, 0)
            )
            pygame.draw.circle(self.screen, emotion_color, (screen_x + 10, screen_y - 10), 4)

        # Update display
        pygame.display.flip()
        self.clock.tick(30)  # Limit to 30 FPS


# Scavenger hunt specific components
class CollectibleComponent(Component):
    """Represents an item that can be collected in the scavenger hunt."""

    name: str
    value: int = 1
    collected: bool = False


class InventoryComponent(Component):
    """Stores collected items."""

    items: Dict[str, int] = {}  # item_name -> count

    async def add_item(self, item_name: str, count: int = 1):
        if item_name in self.items:
            self.items[item_name] += count
        else:
            self.items[item_name] = count

    async def get_total_value(self) -> int:
        return sum(self.items.values())


# Scenario setup
async def setup_scavenger_hunt(registry: Registry) -> None:
    """Set up the scavenger hunt environment."""
    # Create collectible items
    items = [("gold_coin", 5), ("silver_key", 3), ("ancient_scroll", 8), ("magic_crystal", 10), ("rusty_dagger", 2)]

    # Scatter items around the map (100x100 grid)
    for name, value in items:
        # Create multiple instances of each item
        for i in range(3):  # 3 of each item
            item_entity = Entity(registry=registry)
            await item_entity.add_component(CollectibleComponent(name=name, value=value))
            await item_entity.add_component(Position(x=random.uniform(0, 100), y=random.uniform(0, 100)))
            registry.register_entity(item_entity)
            print(f"Created {name} at {item_entity.get_component(Position)}")

    # Create hunter agents
    for i in range(3):
        hunter = Entity(registry=registry)
        # Add spatial components
        await hunter.add_component(Position(x=random.uniform(0, 100), y=random.uniform(0, 100)))
        await hunter.add_component(Velocity(vx=0, vy=0))

        # Add cognitive components
        await hunter.add_component(CognitiveComponent(cognitive_cycle_interval=0.5))
        await hunter.add_component(PerceptionComponent(vision_range=15.0))
        await hunter.add_component(MemoryComponent())
        await hunter.add_component(BeliefSystemComponent())
        await hunter.add_component(RelationshipComponent())
        await hunter.add_component(EmotionalStateComponent())
        await hunter.add_component(GoalComponent())
        await hunter.add_component(MetaCognitionComponent())
        await hunter.add_component(AIMovementController())

        # Add inventory for collecting items
        await hunter.add_component(InventoryComponent())

        # Set initial goal
        goal_component = await hunter.get_component(GoalComponent)
        await goal_component.add_goal(description="find valuable items", priority=GoalPriority.HIGH)

        # Set relationships with other hunters
        # Randomly make hunters friends or enemies
        relationship = await hunter.get_component(RelationshipComponent)
        for j in range(3):
            if i != j:
                rel_type = random.choice([RelationshipType.FRIEND, RelationshipType.ENEMY])
                await relationship.set_relationship(f"hunter_{j}", rel_type)

        registry.register_entity(hunter)
        print(f"Created Hunter {i} at {hunter.get_component(Position)}")


# Custom system for handling item collection
class ScavengerHuntSystem(System):
    """Handles item collection mechanics."""

    async def update(self, delta_time: float = 0) -> None:
        """Check if hunters are near collectibles and collect them."""
        hunters = []
        collectibles = []

        # Get all hunters and collectibles
        async for entity_ref in self.registry.entities_with_components(InventoryComponent):
            hunter = await entity_ref.resolve()
            hunters.append(hunter)

        async for entity_ref in self.registry.entities_with_components(CollectibleComponent):
            collectible = await entity_ref.resolve()
            if not (await collectible.get_component(CollectibleComponent)).collected:
                collectibles.append(collectible)

        # Check for collection
        for hunter in hunters:
            hunter_pos = await hunter.get_component(Position)
            for collectible in collectibles:
                collectible_component = await collectible.get_component(CollectibleComponent)
                if collectible_component.collected:
                    continue

                collectible_pos = await collectible.get_component(Position)

                # Calculate distance
                dx = hunter_pos.x - collectible_pos.x
                dy = hunter_pos.y - collectible_pos.y
                distance = (dx**2 + dy**2) ** 0.5

                # If close enough, collect the item
                if distance < 2.0:  # Collection radius
                    collectible_component.collected = True

                    # Add to inventory
                    inventory = await hunter.get_component(InventoryComponent)
                    await inventory.add_item(collectible_component.name, collectible_component.value)

                    # Store memory of finding the item
                    memory = await hunter.get_component(MemoryComponent)
                    await memory.store_memory(
                        content={
                            "event": "collected_item",
                            "item_name": collectible_component.name,
                            "item_value": collectible_component.value,
                            "location": (collectible_pos.x, collectible_pos.y),
                        },
                        category="collection",
                        saliency=collectible_component.value / 10.0,  # More valuable items create stronger memories
                    )

                    # Experience emotion based on item value
                    emotional = await hunter.get_component(EmotionalStateComponent)
                    if collectible_component.value >= 8:
                        await emotional.feel_emotion(
                            EmotionType.JOY, 0.8, f"Found valuable {collectible_component.name}"
                        )
                    else:
                        await emotional.feel_emotion(EmotionType.CURIOSITY, 0.3, f"Found {collectible_component.name}")

                    # Update belief about item locations
                    beliefs = await hunter.get_component(BeliefSystemComponent)
                    await beliefs.add_or_update_belief(
                        f"Items can be found in region {int(collectible_pos.x // 20)},{int(collectible_pos.y // 20)}",
                        confidence=0.7,
                        evidence=f"Found {collectible_component.name} at ({collectible_pos.x:.1f}, {collectible_pos.y:.1f})",
                    )

                    print(f"Hunter collected {collectible_component.name} worth {collectible_component.value} points!")


# Custom extension of CognitiveSystem for hunt-specific behaviors
class HunterCognitiveSystem(CognitiveSystem):
    """Extends the CognitiveSystem with scavenger hunt specific behaviors."""

    async def _make_decision(self, entity: Entity, situation: Dict[str, Any]) -> Optional[CognitiveAction]:
        """Override decision making with scavenger hunt specific behavior."""
        # First check if any collectible is visible

        for entity_id, perception in situation.get("visual_entities", {}).items():
            # Try to resolve the entity
            async for entity_ref in self.registry.entities_with_id(entity_id):
                target = await entity_ref.resolve()
                collectible = await target.get_component(CollectibleComponent, None)

                if collectible and not collectible.collected:
                    # Found a collectible! Go get it
                    return CognitiveAction(
                        action_type="approach",
                        target_entity_id=entity_id,
                        parameters={"speed": 1.0},
                        priority=0.9,
                        reasoning=f"Moving to collect {collectible.name}",
                    )

        # If we see another hunter, react based on relationship
        for entity_id, perception in situation.get("visual_entities", {}).items():
            async for entity_ref in self.registry.entities_with_id(entity_id):
                target = await entity_ref.resolve()
                if await target.get_component(InventoryComponent, None):
                    # It's another hunter
                    relationship = await entity.get_component(RelationshipComponent)
                    rel_type = await relationship.get_relationship(entity_id)

                    if rel_type == RelationshipType.ENEMY:
                        # Avoid enemy hunters
                        return CognitiveAction(
                            action_type="flee",
                            target_entity_id=entity_id,
                            parameters={"speed": 0.8},
                            priority=0.7,
                            reasoning="Avoiding competitor hunter",
                        )
                    elif rel_type == RelationshipType.FRIEND:
                        # Maybe later we could implement item sharing or information exchange
                        pass

        # Otherwise use the beliefs to guide exploration
        beliefs = await entity.get_component(BeliefSystemComponent)
        rich_regions = await beliefs.get_relevant_beliefs(["found", "region"])

        if rich_regions:
            # Extract region coordinates from the highest confidence belief
            rich_regions.sort(key=lambda b: b.confidence, reverse=True)
            top_belief = rich_regions[0].statement

            # Parse region coordinates (simple parsing assuming format "region X,Y")
            import re

            match = re.search(r"region (\d+),(\d+)", top_belief)
            if match:
                region_x = int(match.group(1))
                region_y = int(match.group(2))

                # Target the center of that region
                center_x = region_x * 20 + 10
                center_y = region_y * 20 + 10

                return CognitiveAction(
                    action_type="move_to",
                    parameters={"target_x": center_x, "target_y": center_y, "speed": 0.6},
                    priority=0.6,
                    reasoning=f"Exploring promising region {region_x},{region_y}",
                )

        # Default to exploration
        return await super()._make_decision(entity, situation)

    async def _execute_action(self, entity: Entity, action: CognitiveAction) -> None:
        """Extend action execution with move_to capability."""
        if action.action_type == "move_to":
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)

            if position and velocity:
                target_x = action.parameters.get("target_x", position.x)
                target_y = action.parameters.get("target_y", position.y)

                # Set velocity toward target
                dx = target_x - position.x
                dy = target_y - position.y
                dist = (dx**2 + dy**2) ** 0.5

                if dist > 0.1:  # Only move if not already at target
                    speed = action.parameters.get("speed", 0.5)
                    velocity.vx = dx / dist * speed
                    velocity.vy = dy / dist * speed
                else:
                    velocity.vx = 0
                    velocity.vy = 0
        else:
            # Use default execution for other actions
            await super()._execute_action(entity, action)


# Main simulation loop
async def run_scavenger_hunt_simulation():
    registry = Registry()

    # Set up the hunt
    await setup_scavenger_hunt(registry)

    # Create systems
    cognitive_system = HunterCognitiveSystem(registry)
    cognitive_proc_system = CognitiveProcessingSystem(registry)

    scavenger_system = ScavengerHuntSystem(registry)
    movement_system = MovementSystem(registry=registry)
    render_system = RenderSystem(registry)  # Add the render system
    movement_task_system = MovementTaskSystem(registry)

    running = True
    step = 0

    # Main loop
    while running:
        print(f"\n--- Simulation Step {step} ---")

        # Update systems
        await movement_system.update(0.5)  # 0.5 time units per step
        await cognitive_system.update()
        await cognitive_proc_system.update()
        await scavenger_system.update()
        await movement_task_system.update()
        await render_system.update()  # Render the current state

        # Display current hunter status every 10 steps
        if step % 10 == 0:
            print("\nCurrent Hunter Status:")
            async for entity_ref in registry.entities_with_components(InventoryComponent):
                hunter = await entity_ref.resolve()
                inventory = await hunter.get_component(InventoryComponent)
                pos = await hunter.get_component(Position)
                emotion = await hunter.get_component(EmotionalStateComponent)

                print(f"Hunter at ({pos.x:.1f}, {pos.y:.1f})")
                print(f"  Items: {inventory.items}")
                print(f"  Value: {await inventory.get_total_value()}")
                print(f"  Emotion: {emotion.dominant_emotion}")

        step += 1
        await asyncio.sleep(0.02)  # Shorter delay for smoother animation

    # Show final results
    print("\n=== FINAL RESULTS ===")
    hunters = []
    async for entity_ref in registry.entities_with_components(InventoryComponent):
        hunter = await entity_ref.resolve()
        inventory = await hunter.get_component(InventoryComponent)
        hunters.append((hunter, await inventory.get_total_value()))

    # Sort by score
    hunters.sort(key=lambda h: h[1], reverse=True)

    # Show rankings
    for i, (hunter, score) in enumerate(hunters):
        inventory = await hunter.get_component(InventoryComponent)
        print(f"#{i + 1}: Hunter with {score} points")
        print(f"  Collected items: {inventory.items}")

    # Keep the window open until user closes it
    if pygame.get_init():
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
        pygame.quit()


# Run the simulation
if __name__ == "__main__":
    asyncio.run(run_scavenger_hunt_simulation())

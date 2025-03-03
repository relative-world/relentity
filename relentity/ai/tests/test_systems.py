from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from relentity.ai.components import AIDriven
from relentity.ai.pydantic_ollama.responses import BasicResponse
from relentity.ai.systems import AIDrivenSystem
from relentity.core import Registry, Entity, Identity


@pytest.fixture
def registry():
    return Registry()


@pytest.fixture
def system(registry):
    return AIDrivenSystem(registry)


@pytest.mark.asyncio
async def test_update(system, registry):
    entity = Entity(registry)
    await entity.add_component(Identity(name="Test Entity", description="Test description"))
    await entity.add_component(AIDriven(model="test-model", update_interval=1))
    registry.register_entity(entity)
    with patch.object(system, "process_entity", new_callable=AsyncMock) as mock_process_entity:
        await system.update()
        mock_process_entity.assert_awaited_once_with(entity)


@pytest.mark.asyncio
async def test_process_entity(system, registry):
    entity = Entity[
        Identity(name="Test Entity", description="Test description"), AIDriven(model="test-model", update_interval=1)
    ](registry)

    with patch.object(system._client, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = (MagicMock(), BasicResponse(text="Test response"))
        response = await system.process_entity(entity)
        assert response.text == "Test response"
        assert (await entity.get_component(AIDriven))._update_count == 1

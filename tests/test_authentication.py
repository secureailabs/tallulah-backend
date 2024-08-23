import pytest
import conftest
from conftest import logger


@pytest.mark.asyncio
async def test_me(client, token):
    # token = test_login(client, test_user)
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    logger.info(response.json())
    assert response.status_code == 200

import pytest
import conftest
from conftest import logger


@pytest.fixture(scope='module')
async def get_all_form_templates(client, token):
    response = client.get("/api/form-templates/", headers={"Authorization": f"Bearer {token}"})
    logger.info(response.json())
    assert response.status_code == 200
    return response.json()["templates"]


async def test_get_all_form_data(client, token, get_all_form_templates):
    response = client.put("/api/form-data/", params={"form_template_id": get_all_form_templates[0]["id"]}, headers={"Authorization": f"Bearer {token}"})
    logger.info(response.json())
    assert response.status_code == 200
    assert len(response.json()["form_data"]) > 0

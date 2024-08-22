from fastapi.testclient import TestClient
from app.main import server
import pytest
import logging
import os

# client = TestClient(server)
logger = logging.getLogger("pytest-logs")

@pytest.fixture(scope='session')
def client():
    with TestClient(server) as c:
      yield c


@pytest.fixture(scope='session')
def test_user():
    return {"username": os.getenv("TEST_USER"), "password": os.getenv("TEST_PASSWORD")}


@pytest.fixture(scope='session')
def token(client, test_user):
    response = client.post("/api/login", data=test_user)
    logger.info(response.json())
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None
    return token

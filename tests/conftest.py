import pytest
from faker import Faker
from rest_framework.test import APIClient


@pytest.fixture
def api():
    return APIClient()


# Semilla global para datos de Faker reproducibles
@pytest.fixture(autouse=True, scope="session")
def faker_seed():
    Faker.seed(12345)

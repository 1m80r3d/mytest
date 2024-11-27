import os
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from app.processing.models import Bbox
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def bbox() -> Bbox:
    return Bbox(
            min_x=27.37,
            max_x=27.42,
            min_y=44.15,
            max_y=44.20
        )

@pytest.fixture
def get_data_file_path() -> Callable:
    def fixtures_file_path(file_name):
        current_path = os.path.dirname(os.path.realpath(__file__))
        data_path = os.path.join(current_path, "test_data")
        return os.path.join(data_path, file_name)

    return fixtures_file_path

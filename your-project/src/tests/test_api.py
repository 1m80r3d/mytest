import hashlib
import json
from typing import Callable
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert 200 == response.status_code
    assert {"status": "I'm alive"} == response.json()


def test_bbox(client: TestClient, get_data_file_path: Callable):
    response = client.get("/date/20160501/crop_by_bounding_box?min_x=27.37&max_x=27.42&min_y=44.15&max_y=44.20")
    assert 200 == response.status_code
    result = hashlib.md5(response.content)
    assert result.hexdigest() == "6f6ea41cf6a6d3de8b336dd4a1d8894e"


def test_json(client: TestClient, get_data_file_path: Callable):
    geo_json = get_data_file_path("geometry_cut.geojson")
    with open(geo_json, "r") as json_file:
        data = json_file.read()
    json_data = json.loads(data)
    response = client.post(url="/date/20160501/crop_by_geojson", json=json_data)
    assert 200 == response.status_code
    result = hashlib.md5(response.content)
    assert result.hexdigest() ==  "8ddbec3f3c1f5feb77b445d452a825ee"


def test_image_exception(client: TestClient):
    response = client.get(url="/date/xxxx/crop_by_bounding_box?min_x=27.37&max_x=27.42&min_y=44.15&max_y=44.20")
    assert 400 == response.status_code
    assert response.json()['error'] == "image not found"

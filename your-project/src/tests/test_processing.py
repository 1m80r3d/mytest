import hashlib
import json

from app.processing.cutter import CropBBox, CropJson


def test_bbox_model(bbox):
     assert bbox.get_bbox() == (27.37, 44.15, 27.42, 44.2)


def test_processing_cut(bbox, get_data_file_path):
    input_raster = get_data_file_path("20160501.tif")
    cropper = CropBBox(ds_path=input_raster)
    bytes = cropper.crop(bbox)
    result = hashlib.md5(bytes.getbuffer())
    assert result.hexdigest() ==  "6f6ea41cf6a6d3de8b336dd4a1d8894e"


def test_geojson(get_data_file_path):
    input_raster = get_data_file_path("20160501.tif")
    geom_file = get_data_file_path("geometry_cut.geojson")

    with open(geom_file, 'r') as file:
        data = json.load(file)

    cropper = CropJson(ds_path=input_raster)
    bytes = cropper.crop(geom=data)
    result = hashlib.md5(bytes.getbuffer())
    assert result.hexdigest() ==  "8ddbec3f3c1f5feb77b445d452a825ee"
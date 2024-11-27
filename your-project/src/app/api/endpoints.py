import os
from typing import Annotated

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import StreamingResponse

from app.api.models import BboxRequest
from app.processing.cutter import CropBBox, CropJson
from app.processing.models import Bbox
from app.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "I'm alive"}


@router.get("/date/{image}/crop_by_bounding_box")
async def crop_by_bounding_box(image: str, box_query: Annotated[BboxRequest, Query()]) -> StreamingResponse:
    settings = get_settings()
    ds_path = os.path.join(settings.IMG_PATH, f"{image}.tif")
    cropper = CropBBox(ds_path=ds_path)
    bbox = Bbox(
        min_x = box_query.min_x,
        max_x = box_query.max_x,
        min_y = box_query.min_y,
        max_y = box_query.max_y

    )
    mem_file = cropper.crop(bbox)
    return StreamingResponse(
        mem_file,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=output.tif"}
    )


@router.post("/date/{image}/crop_by_geojson")
async def crop_by_bounding_box(image: str, request: Request) -> StreamingResponse:
    settings = get_settings()
    geo_json = await request.json()
    ds_path = os.path.join(settings.IMG_PATH, f"{image}.tif")
    cropper = CropJson(ds_path=ds_path)
    mem_file = cropper.crop(geo_json)
    return StreamingResponse(
        mem_file,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=output.tif"}
    )

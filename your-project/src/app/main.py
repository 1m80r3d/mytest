from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from osgeo import gdal
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.api import api_router
from app.api.endpoints import router as root_router
from app.processing.exceptions import ImageNotFound

gdal.UseExceptions()


app = FastAPI(title="crop")


@app.exception_handler(ImageNotFound)
async def image_exception_handler(_request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"error":"image not found", "detail": str(exc)})
    )

app.include_router(root_router)
app.include_router(api_router)


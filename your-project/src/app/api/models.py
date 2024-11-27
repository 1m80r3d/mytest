from pydantic import BaseModel, Field, field_validator


class BboxRequest(BaseModel):
    min_x: float = Field(
        description="Min Longitude"
    )
    max_x: float = Field(
        description="Max Latitude"
    )
    min_y: float = Field(
        description="Max Longitude"
    )
    max_y: float = Field(
        description="Max Latitude"
    )

from pydantic import BaseModel


class Bbox(BaseModel):
    """
    Bbox Model class.
    """

    min_x: float
    max_x: float
    min_y: float
    max_y: float

    def get_bbox(self) -> tuple[float, float, float, float]:
        return self.min_x, self.min_y, self.max_x, self.max_y,


class BboxTransformed(BaseModel):
    """
    BboxTransformed Model class.
    """

    offset_x: int
    offset_y: int
    size_x: int
    size_y: int

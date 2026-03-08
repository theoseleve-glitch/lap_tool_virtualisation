from pydantic import BaseModel


class ExtractionRequest(BaseModel):
    venue_slug: str
    imagery_version: int
    crop_version: int
    run_id: str
    image_npy_path: str
    pixel_size_m: float = 0.25

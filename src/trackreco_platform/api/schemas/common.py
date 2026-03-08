from datetime import datetime

from pydantic import BaseModel


class ErrorEnvelope(BaseModel):
    error: dict


class JobState(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    error_code: str | None = None
    error_message: str | None = None

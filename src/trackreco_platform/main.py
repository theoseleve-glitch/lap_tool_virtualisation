from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
import uvicorn

from trackreco_platform.api.routes import crops, imagery, layouts, venues
from trackreco_platform.config import settings
from trackreco_platform.errors import DomainError
from trackreco_platform.logging import configure_logging

configure_logging()

app = FastAPI(title="TrackReco Layout Registry", version="0.2.0")
app.include_router(venues.router, prefix=settings.api_prefix)
app.include_router(imagery.router, prefix=settings.api_prefix)
app.include_router(crops.router, prefix=settings.api_prefix)
app.include_router(layouts.router, prefix=settings.api_prefix)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError):
    return ORJSONResponse(status_code=400, content={"error": {"code": exc.code, "message": exc.message, "details": exc.details or {}}})


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def run() -> None:
    uvicorn.run("trackreco_platform.main:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    run()

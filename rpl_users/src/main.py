import os
import sys
from datetime import timezone
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from shared.dtos import ErrorResponseDTO

# Add root to sys.path to import shared
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))
from shared.logger import setup_logger

log_path = os.path.join(os.path.dirname(__file__), "../../../../logs/users.log")
logger = setup_logger("rpl_users", log_file=log_path)

from rpl_users.src.config.api_metadata import FASTAPI_METADATA
from rpl_users.src.routers.users import router as users_router
from rpl_users.src.routers.courses import router as courses_router


app = FastAPI(**FASTAPI_METADATA)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error = ErrorResponseDTO(detail=str(exc.detail), error_code=f"HTTP_{exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error.model_dump(mode="json")
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error = ErrorResponseDTO(detail="Internal Server Error", error_code="INTERNAL_ERROR")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump(mode="json")
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting RPL Users API")

app.add_middleware(
    # CORSMiddleware, allow_origins=["http://localhost:3000","http://localhost:8088"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


app.include_router(users_router)
app.include_router(courses_router)


# ==============================================================================


@app.get("/", include_in_schema=False)
def root_docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/api/v3/health")
def health_ping():
    return "pong"

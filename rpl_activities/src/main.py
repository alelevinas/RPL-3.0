import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Add root to sys.path to import shared
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))
from shared.logger import setup_logger

log_path = os.path.join(os.path.dirname(__file__), "../../../../logs/activities.log")
logger = setup_logger("rpl_activities", log_file=log_path)

from rpl_activities.src.config.api_metadata import FASTAPI_METADATA
from rpl_activities.src.config.api_lifespan import users_api_conn_lifespan
from rpl_activities.src.routers.categories import router as categories_router
from rpl_activities.src.routers.rpl_files import router as rplfiles_router
from rpl_activities.src.routers.activities import router as activities_router
from rpl_activities.src.routers.activity_tests import router as activity_tests_router
from rpl_activities.src.routers.submissions import router as submissions_router
from rpl_activities.src.routers.stats import router as stats_router


app = FastAPI(lifespan=users_api_conn_lifespan, **FASTAPI_METADATA)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting RPL Activities API")


app.add_middleware(
    # CORSMiddleware, allow_origins=["http://localhost:3000","http://localhost:8088"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

app.include_router(categories_router)
app.include_router(rplfiles_router)
app.include_router(activities_router)
app.include_router(activity_tests_router)
app.include_router(submissions_router)
app.include_router(stats_router)


# ==============================================================================


@app.get("/", include_in_schema=False)
def root_docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/api/v3/health")
def health_ping():
    return "pong"

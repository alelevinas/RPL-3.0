from datetime import timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from rpl_users.src.config.api_metadata import FASTAPI_METADATA
from rpl_users.src.routers.users import router as users_router
from rpl_users.src.routers.courses import router as courses_router


app = FastAPI(**FASTAPI_METADATA)

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

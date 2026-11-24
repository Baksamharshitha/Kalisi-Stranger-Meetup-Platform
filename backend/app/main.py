from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.config import settings
from app.api.api import api_router
from app.admin_dashboard import admin_router
from app.db.database import Base, engine, SessionLocal
from app.services.seed_data import seed_database

# Create tables
Base.metadata.create_all(bind=engine)

# Auto seed on startup
with SessionLocal() as db:
    seed_database(db)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# CORS middleware for Flutter web/mobile development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Mobile & Client APIs
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include Admin Dashboard Web routes directly
app.include_router(admin_router)

@app.get("/", response_class=HTMLResponse)
def root_redirect():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Kalisi Platform</title>
        <meta http-equiv="refresh" content="0; url=/admin" />
      </head>
      <body style="background:#121212; color:#fff; font-family:sans-serif; text-align:center; padding-top:20vh;">
        <h2>Redirecting to Kalisi Admin Control Center...</h2>
        <p><a href="/admin" style="color:#F5A623;">Click here if not redirected</a></p>
      </body>
    </html>
    """)

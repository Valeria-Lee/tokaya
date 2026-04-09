"""
main.py — Robyn application entry point.

Startup creates all tables (use Alembic in production instead).
X-User-Id header is extracted in each route since Robyn doesn't have
FastAPI-style dependency injection — use a helper function instead.
"""

from robyn import Robyn, Request, Response
from sqlalchemy import text

from database import engine, get_session
from models import Base

app = Robyn(__file__)


# ---------------------------------------------------------------------------
# Startup / teardown
# ---------------------------------------------------------------------------

@app.startup_handler
async def startup():
    """Create tables on startup. Replace with Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.shutdown_handler
async def shutdown():
    await engine.dispose()


# ---------------------------------------------------------------------------
# Auth helper — API Gateway injects X-User-Id, we just read it
# ---------------------------------------------------------------------------

def get_user_id(request: Request) -> str:
    user_id = request.headers.get("x-user-id", "").strip()
    if not user_id:
        raise ValueError("Missing X-User-Id header")
    return user_id


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health(request: Request):
    async with get_session() as session:
        await session.execute(text("SELECT 1"))
    return Response(status_code=200, headers={}, description='{"status":"ok"}')


# ---------------------------------------------------------------------------
# Register routers (add as you build each feature)
# ---------------------------------------------------------------------------

# from routers.tokayo   import tokayo_router
# from routers.minigame import minigame_router
# app.include_router(tokayo_router)
# app.include_router(minigame_router)


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=8080)

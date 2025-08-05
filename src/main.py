from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routes import webhooks
from .settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Initialize database, clients, and other resources
    print("Starting up AutoMailHelpdesk...")
    yield
    # TODO: Clean up resources
    print("Shutting down AutoMailHelpdesk...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(webhooks.router)


@app.get("/healthz", tags=["Health Check"])
async def healthz():
    # TODO: Implement actual health check logic
    return {"status": "ok"}


@app.get("/readyz", tags=["Health Check"])
async def readyz():
    # TODO: Implement actual readiness check logic (e.g., database connection, external APIs)
    return {"status": "ready"}


# TODO: Add more routes and application logic as needed



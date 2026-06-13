from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medibot.api.routes import (
    auth_router,
    chat_router,
    collections_router,
    health_router,
)

app = FastAPI(
    title="MediBot API",
    description="Backend API for MediBot - Medical RAG and RBAC assistant",
    version="1.0.0",
)

# Configure CORS to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Next.js or local dev origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with appropriate prefixes
app.include_router(health_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(collections_router)
app.include_router(chat_router)

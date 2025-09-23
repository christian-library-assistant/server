import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import router
from ..config.settings import ANTHROPIC_API_KEY
from ..infrastructure.ai_clients.anthropic import AnthropicClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Smart Library Assistant API", debug=True)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    # Initialize AI client
    anthropic_client = AnthropicClient(api_key=ANTHROPIC_API_KEY)

    # Store the client in app state for dependency injection
    app.state.anthropic_client = anthropic_client

    # Include API routes
    app.include_router(router)

    @app.get("/")
    def read_root():
        return {"message": "Smart Library Assistant API"}

    @app.get("/health/")
    def health_check():
        return {"message": "Server is running"}

    return app
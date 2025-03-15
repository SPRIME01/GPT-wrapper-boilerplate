from contextlib import asynccontextmanager
from fastapi import FastAPI
from strawberry.asgi import GraphQL
from app.infrastructure.adapters.http.graphql_schema import schema
from app.infrastructure.adapters.http.fastapi_controllers import router
from app.infrastructure.container import Container

# Create and configure the container
container = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize resources
    container.wire(
        modules=[
            "app.infrastructure.adapters.http.graphql_schema",
            "app.infrastructure.adapters.http.fastapi_controllers"
        ]
    )
    yield
    # Shutdown: Cleanup resources
    container.unwire()

# Create FastAPI application with lifespan handler
app = FastAPI(
    title="GPT API",
    description="API for interacting with GPT models",
    lifespan=lifespan
)

# Include REST API routes
app.include_router(router)

# Add GraphQL endpoint
graphql_app = GraphQL(schema)
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

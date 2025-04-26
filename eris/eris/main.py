from fastapi import FastAPI, Depends, APIRouter
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from eris.api.v1 import eris
from eris.database import engine, Base
from eris.database.repository import TaskRepository, ProcessRepository
from eris.api.auth import verify_credentials

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Initialize repositories
task_repo = TaskRepository()
process_repo = ProcessRepository()

app = FastAPI(
    title="Eris API",
    description="API for the Eris attack simulation subsystem of Jano",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mainrouter = APIRouter(tags=["main"])

# Root path to verify the API is running
@mainrouter.get("/", response_class=HTMLResponse)
async def main_page():
    """List of html endpoints for Swagger and Redoc."""

    return """
    <html>
    <head>
        <title>Eris API</title>
    </head>
    <body>
        <h1>Welcome to Eris API</h1>
        <p>The antagonist security testing component of Jano.</p>
        <p>Check out the API documentation:</p>
        <ul>
            <li><a href="/docs">Swagger</a></li>
            <li><a href="/redoc">Redoc</a></li>
        </ul>
    </body>
    </html>
    """

app.include_router(mainrouter)
app.include_router(eris.router, dependencies=[Depends(verify_credentials)])
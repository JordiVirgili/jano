from fastapi import FastAPI, Depends, APIRouter

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from argos.api.v1 import tasks, chat, argos, fix_api
from argos.api.v1 import utils
from argos.database import engine, Base
from argos.database.repository import TaskRepository, ProcessRepository, ChatSessionRepository, ChatMessageRepository
from argos.api.auth import verify_credentials

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Initialize repositories
task_repo = TaskRepository()
process_repo = ProcessRepository()
chat_session_repo = ChatSessionRepository()
chat_message_repo = ChatMessageRepository()

app = FastAPI(title="Jano API",
              description="API for the Jano AI-powered security configuration system",
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
        <title>Argos API</title>
    </head>
    <body>
        <h1>Welcome to Argos API</h1>
        <p>Check out the API documentation:</p>
        <ul>
            <li><a href="/docs">Swagger</a></li>
            <li><a href="/redoc">Redoc</a></li>
        </ul>
    </body>
    </html>
    """

app.include_router(mainrouter)
app.include_router(utils.router, dependencies=[Depends(verify_credentials)])
app.include_router(tasks.router, dependencies=[Depends(verify_credentials)])
app.include_router(chat.router, dependencies=[Depends(verify_credentials)])
app.include_router(argos.router, dependencies=[Depends(verify_credentials)])
app.include_router(fix_api.router, dependencies=[Depends(verify_credentials)])
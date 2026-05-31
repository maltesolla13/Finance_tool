from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.app.database.db_config import init_db
from backend.app.services.apis.backend_api import BackendRoutes
from backend.app.services.scheduler import install_jobs

# Starten:
# --- Backend ---
# .\venv\Scripts\Activate.ps1
# python -m uvicorn main:app --reload
# --- Frontend ---
# cd frontend
# npm start


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Guard gegen Doppelstart (z. B. durch uvicorn --reload)
    if not getattr(app.state, "scheduler_installed", False):
        install_jobs(app)
        app.state.scheduler_installed = True
    yield
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler and scheduler.running:
        scheduler.shutdown()

app = FastAPI(title="Finance Tool API", lifespan=lifespan)

# CORS – passe Origins an dein Frontend an (Vite: 5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # optional für CRA:
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# >>> Globales API-Prefix
routes = BackendRoutes()
app.include_router(BackendRoutes().router, prefix="/financetool/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

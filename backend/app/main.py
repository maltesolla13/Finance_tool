from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db_config import init_db
from app.services.backend_api import BackendRoutes

app = FastAPI(title="Finance Tool API")


@app.lifespan("startup")
def _startup():
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(BackendRoutes().router)

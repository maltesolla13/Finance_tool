from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.app.database.db_config import init_db
from backend.app.services.backend_api import BackendRoutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

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
app.include_router(routes.router, prefix="/financetool/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# app = FastAPI(title="Finance Tool API")
#
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # == STARTUP ==
#     init_db()  # sync ist okay hier
#     yield
#     # == SHUTDOWN ==
#     # optional: Ressourcen schließen / Cleanup
#
# app = FastAPI(title="Finance Tool API", lifespan=lifespan)
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# app.include_router(BackendRoutes().router)
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "main:app",
#         host="127.0.0.1",
#         port=8000, reload=True
#     )

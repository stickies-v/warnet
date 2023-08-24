from fastapi import FastAPI, APIRouter
from routers import warnet

app = FastAPI()

base_router = APIRouter(
    prefix="/api/v1"
)

base_router.include_router(warnet.router)

app.include_router(base_router)
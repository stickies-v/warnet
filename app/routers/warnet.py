from enum import Enum
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class WarnetStatus(Enum):
    running = "running"
    stopped = "stopped"


class WarnetModel(BaseModel):
    id: int = 0
    status: WarnetStatus = WarnetStatus.stopped

warnets = []  # TODO: persist?


router = APIRouter(
    prefix="/warnet"
)


@router.get("/", tags=["warnet"])
async def list_warnets():
    return warnets


@router.post("/", tags=["warnet"])
async def create_warnet(warnet: WarnetModel):
    if warnets:
        # Temporary restriction: only allow 1 warnet
        raise HTTPException(status_code=400, detail="Only 1 warnet can be constructed")

    warnets.append(warnet)
    return warnet


@router.get("/{warnet_id}")
async def get_warnet(warnet_id: int):
    return warnets[warnet_id]

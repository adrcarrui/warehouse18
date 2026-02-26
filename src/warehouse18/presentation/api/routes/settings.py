from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from warehouse18.infrastructure.db import get_db

router = APIRouter(prefix="/settings", tags=["settings"])

class RfidSettingsOut(BaseModel):
    create_movements: bool

class RfidSettingsIn(BaseModel):
    create_movements: bool

@router.get("/rfid", response_model=RfidSettingsOut)
def get_rfid_settings(request: Request, db: Session = Depends(get_db)):
    svc = request.app.state.settings_service
    return {"create_movements": svc.get_rfid_create_movements(db)}

@router.put("/rfid", response_model=RfidSettingsOut)
def set_rfid_settings(body: RfidSettingsIn, request: Request, db: Session = Depends(get_db)):
    svc = request.app.state.settings_service
    v = svc.set_rfid_create_movements(db, body.create_movements)
    return {"create_movements": v}
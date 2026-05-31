from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.beam import Beam, BeamStatus
from backend.schemas.beam import BeamResponse
from backend.api.deps import get_current_user

router = APIRouter(prefix="/beams", tags=["Beams"])


@router.get("/", response_model=List[BeamResponse])
def list_beams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Beam).all()


@router.get("/free", response_model=List[BeamResponse])
def list_free_beams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Beam).filter(Beam.status == BeamStatus.AVAILABLE).all()


@router.get("/{beam_id}", response_model=BeamResponse)
def get_beam(beam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    beam = db.query(Beam).filter(Beam.id == beam_id).first()
    if not beam:
        raise HTTPException(status_code=404, detail="Beam not found")
    return beam

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.beam import Beam, BeamStatus
from backend.schemas.beam import BeamResponse
from backend.api.deps import get_current_user, require_po_access

router = APIRouter(prefix="/beams", tags=["Beams"])


@router.get("/", response_model=List[BeamResponse])
def list_beams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Beam).all()


@router.get("/free", response_model=List[BeamResponse])
def list_free_beams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Beam).filter(Beam.status == BeamStatus.AVAILABLE).all()


@router.get("/po/{po_number}/cycle/{cycle_number}", response_model=List[BeamResponse])
def beams_for_cycle(po_number: str, cycle_number: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_po_access(po_number, db, current_user)
    return db.query(Beam).filter(
        Beam.po_number == po_number, Beam.cycle_number == cycle_number
    ).all()


@router.get("/available", response_model=List[BeamResponse])
def list_available_beams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Beam).filter(Beam.status == BeamStatus.AVAILABLE).all()


@router.get("/{beam_id}", response_model=BeamResponse)
def get_beam(beam_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    beam = db.query(Beam).filter(Beam.id == beam_id).first()
    if not beam:
        raise HTTPException(status_code=404, detail="Beam not found")
    require_po_access(beam.po_number, db, current_user)
    return beam
